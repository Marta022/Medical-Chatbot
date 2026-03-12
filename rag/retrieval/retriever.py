"""Retrieval orchestration for vector and hybrid modes.

Core responsibilities:
- Build vector search hits from Qdrant.
- Optionally enrich retrieval with graph traversal hits.
- Apply policy controls from request filters (mode, depth, weights).
- Apply keyword fallback when vector confidence is too low.
- Rerank candidates with lexical overlap while keeping semantic score dominant.

Entrypoint:
- `retrieve_top_similar(...)` chooses retrieval mode and returns `RetrievalResult`.
"""

from __future__ import annotations

import re
from typing import Any

from qdrant_client.models import FieldCondition, Filter, MatchValue

from config.settings import SETTINGS
from knowledge.entities.extractor import extract_entities_from_chunk, load_disease_terms
from knowledge.graph import get_graph_client
from knowledge.qdrant.client import COLLECTION, client
from models import PdfStructuredChunk, RetrievalHit, RetrievalResult
from rag.retrieval.embeddings import embed_query

_POLICY_GRAPH_DEPTH_KEY = "__graph_depth"
_POLICY_VECTOR_WEIGHT_KEY = "__vector_weight"
_POLICY_GRAPH_WEIGHT_KEY = "__graph_weight"
_POLICY_RETRIEVAL_MODE_KEY = "__retrieval_mode"
_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def _build_filter(filter_by: dict[str, str] | None) -> Filter | None:
    if not filter_by:
        return None
    conditions = [
        FieldCondition(key=key, match=MatchValue(value=value))
        for key, value in filter_by.items()
        if value is not None and not key.startswith("__")
    ]
    if not conditions:
        return None
    return Filter(must=conditions)


def _tokenize(text: str) -> set[str]:
    return {
        token.lower()
        for token in _TOKEN_PATTERN.findall(text or "")
        if len(token) >= 3
    }


def _rerank_hits(
    query: str,
    hits: list[RetrievalHit],
    *,
    top_k: int,
) -> list[RetrievalHit]:
    if not hits:
        return []
    query_tokens = _tokenize(query)
    if not query_tokens:
        return hits[:top_k]

    weighted: list[tuple[float, RetrievalHit]] = []
    for hit in hits:
        hit_tokens = _tokenize(f"{hit.title} {hit.text}")
        overlap = len(query_tokens.intersection(hit_tokens))
        overlap_ratio = overlap / len(query_tokens)
        # Keep semantic score dominant, but boost query-term alignment.
        rerank_score = (hit.score * 0.85) + (overlap_ratio * 0.15)
        weighted.append((rerank_score, hit))
    return [pair[1] for pair in sorted(weighted, key=lambda item: item[0], reverse=True)[:top_k]]


def _vector_hits(
    input_message: str,
    top_k: int = 5,
    filter_by: dict[str, str] | None = None,
) -> list[RetrievalHit]:
    query_vector = embed_query(input_message)
    payload_filter = _build_filter(filter_by)

    hits = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
        query_filter=payload_filter,
    )

    retrieval_hits: list[RetrievalHit] = []
    for hit in hits:
        payload = hit.payload or {}
        retrieval_hits.append(
            RetrievalHit(
                title=str(payload.get("title", "unknown")).strip(),
                text=str(payload.get("text", "")).strip(),
                score=float(hit.score),
                source=str(payload.get("source", "unknown")),
                source_file=(
                    str(payload.get("source_file")) if payload.get("source_file") is not None else None
                ),
                page=int(payload.get("page")) if payload.get("page") is not None else None,
                section=str(payload.get("section")) if payload.get("section") is not None else None,
                chunk_id=str(payload.get("chunk_id")) if payload.get("chunk_id") is not None else None,
            )
        )
    return retrieval_hits


def _keyword_fallback_hits(
    input_message: str,
    *,
    top_k: int,
    filter_by: dict[str, str] | None = None,
) -> list[RetrievalHit]:
    query_tokens = _tokenize(input_message)
    if not query_tokens:
        return []

    payload_filter = _build_filter(filter_by)
    points, _ = client.scroll(
        collection_name=COLLECTION,
        with_payload=True,
        query_filter=payload_filter,
        limit=max(top_k, SETTINGS.keyword_fallback_candidate_limit),
    )

    scored: list[tuple[float, RetrievalHit]] = []
    query_phrase = " ".join(sorted(query_tokens))
    for point in points:
        payload = point.payload or {}
        title = str(payload.get("title", "unknown")).strip()
        text = str(payload.get("text", "")).strip()
        if not text:
            continue
        hit_tokens = _tokenize(f"{title} {text}")
        if not hit_tokens:
            continue
        overlap = len(query_tokens.intersection(hit_tokens))
        if overlap == 0:
            continue
        overlap_ratio = overlap / max(len(query_tokens), 1)
        phrase_bonus = 0.2 if query_phrase and query_phrase in text.lower() else 0.0
        score = min(overlap_ratio + phrase_bonus, 1.0)
        if score < SETTINGS.keyword_fallback_min_score:
            continue
        scored.append(
            (
                score,
                RetrievalHit(
                    title=title,
                    text=text,
                    score=score,
                    source="keyword_fallback",
                    source_file=(
                        str(payload.get("source_file")) if payload.get("source_file") is not None else None
                    ),
                    page=int(payload.get("page")) if payload.get("page") is not None else None,
                    section=str(payload.get("section")) if payload.get("section") is not None else None,
                    chunk_id=str(payload.get("chunk_id")) if payload.get("chunk_id") is not None else None,
                ),
            )
        )

    ordered = sorted(scored, key=lambda item: item[0], reverse=True)
    return [item[1] for item in ordered[:top_k]]


def _query_seed_entities(input_message: str) -> list[str]:
    disease_terms = load_disease_terms(SETTINGS.dataset_json_path)
    pseudo_chunk = PdfStructuredChunk(
        source_file="query",
        page=0,
        chapter="query",
        section="query",
        chunk_id="query",
        text=input_message,
        is_list=False,
    )
    entities = extract_entities_from_chunk(
        pseudo_chunk,
        disease_terms=disease_terms,
        min_confidence=SETTINGS.entity_min_confidence,
    )
    ordered_unique: list[str] = []
    seen: set[str] = set()
    for entity in entities:
        if entity.canonical_form in seen:
            continue
        seen.add(entity.canonical_form)
        ordered_unique.append(entity.canonical_form)
    return ordered_unique


def _result_to_rows(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []
    if isinstance(result, list):
        rows: list[dict[str, Any]] = []
        for item in result:
            if isinstance(item, dict):
                rows.append(item)
            elif hasattr(item, "_asdict"):
                rows.append(dict(item._asdict()))
        return rows

    to_df = getattr(result, "to_df", None)
    if callable(to_df):
        frame = to_df()
        to_dict = getattr(frame, "to_dict", None)
        if callable(to_dict):
            records = to_dict(orient="records")
            if isinstance(records, list):
                return [item for item in records if isinstance(item, dict)]

    has_next = getattr(result, "has_next", None)
    get_next = getattr(result, "get_next", None)
    if callable(has_next) and callable(get_next):
        rows: list[dict[str, Any]] = []
        while result.has_next():
            item = result.get_next()
            if isinstance(item, dict):
                rows.append(item)
            elif hasattr(item, "_asdict"):
                rows.append(dict(item._asdict()))
        return rows
    return []


def _graph_hits(
    input_message: str,
    *,
    graph_top_k: int,
    traversal_depth: int,
) -> list[RetrievalHit]:
    seed_entities = _query_seed_entities(input_message)
    if not seed_entities:
        return []

    graph_client = get_graph_client()
    try:
        rows: list[dict[str, Any]] = []
        frontier = seed_entities
        visited: set[str] = set(seed_entities)
        max_depth = max(1, traversal_depth)
        for _ in range(max_depth):
            if not frontier:
                break
            next_frontier: list[str] = []
            for canonical_form in frontier:
                result = graph_client.execute(
                    (
                        "MATCH (a:Entity)-[r]->(b:Entity) "
                        "WHERE a.canonical_form = $canonical_form "
                        "RETURN a.canonical_form AS source_entity, "
                        "label(r) AS relation_label, "
                        "b.canonical_form AS target_entity, "
                        "r.source_file AS source_file, "
                        "r.page AS page, "
                        "r.chunk_id AS chunk_id, "
                        "r.confidence AS confidence "
                        "LIMIT $limit;"
                    ),
                    {"canonical_form": canonical_form, "limit": graph_top_k},
                )
                parsed_rows = _result_to_rows(result)
                rows.extend(parsed_rows)
                for row in parsed_rows:
                    target_entity = str(row.get("target_entity", "")).strip()
                    if not target_entity or target_entity in visited:
                        continue
                    visited.add(target_entity)
                    next_frontier.append(target_entity)
            frontier = next_frontier
    finally:
        graph_client.close()

    hits: list[RetrievalHit] = []
    for row in rows:
        source_entity = str(row.get("source_entity", "")).strip()
        target_entity = str(row.get("target_entity", "")).strip()
        relation = str(row.get("relation_label", "")).strip().lower()
        source_file = str(row.get("source_file", "graph")).strip() or "graph"
        page = row.get("page", "unknown")
        chunk_id = str(row.get("chunk_id", "unknown")).strip() or "unknown"
        confidence = float(row.get("confidence", 0.7) or 0.7)
        if not source_entity or not target_entity:
            continue

        hits.append(
            RetrievalHit(
                title=f"Graph relation: {source_entity}",
                text=(
                    f"{source_entity} -[{relation}]-> {target_entity} "
                    f"(source: {source_file}, page: {page}, chunk: {chunk_id})"
                ),
                score=max(0.0, min(1.0, confidence)),
                source="graph",
                source_file=source_file,
                page=int(page) if isinstance(page, int) else None,
                section=None,
                chunk_id=chunk_id,
            )
        )
    return hits


def _merge_hits(
    vector_hits: list[RetrievalHit],
    graph_hits: list[RetrievalHit],
    *,
    top_k: int,
    vector_weight: float,
    graph_weight: float,
) -> list[RetrievalHit]:
    weighted: list[tuple[float, RetrievalHit]] = []
    for hit in vector_hits:
        weighted.append((hit.score * vector_weight, hit))
    for hit in graph_hits:
        weighted.append((hit.score * graph_weight, hit))
    merged = [item[1] for item in sorted(weighted, key=lambda pair: pair[0], reverse=True)]
    deduped: list[RetrievalHit] = []
    seen: set[tuple[str, str, str]] = set()
    for hit in merged:
        key = (hit.source, hit.title, hit.text)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hit)
        if len(deduped) >= top_k:
            break
    return deduped


def retrieve_hybrid(
    input_message: str,
    top_k: int = 5,
    filter_by: dict[str, str] | None = None,
    *,
    graph_top_k: int | None = None,
) -> RetrievalResult:
    vector_hits = _vector_hits(input_message, top_k=top_k, filter_by=filter_by)
    control_filter = filter_by or {}
    graph_depth = int(control_filter.get(_POLICY_GRAPH_DEPTH_KEY, SETTINGS.graph_traversal_depth))
    vector_weight = float(
        control_filter.get(_POLICY_VECTOR_WEIGHT_KEY, SETTINGS.hybrid_vector_weight)
    )
    graph_weight = float(control_filter.get(_POLICY_GRAPH_WEIGHT_KEY, SETTINGS.hybrid_graph_weight))
    graph_hits: list[RetrievalHit] = []
    try:
        graph_hits = _graph_hits(
            input_message,
            graph_top_k=graph_top_k or SETTINGS.graph_retrieval_top_k,
            traversal_depth=graph_depth,
        )
    except Exception:
        graph_hits = []
    merged = _merge_hits(
        vector_hits,
        graph_hits,
        top_k=max(top_k, SETTINGS.retrieval_rerank_top_k),
        vector_weight=vector_weight,
        graph_weight=graph_weight,
    )
    provenance = "hybrid"
    if SETTINGS.keyword_fallback_enabled and (
        not merged or max(hit.score for hit in merged) < SETTINGS.retrieval_min_score
    ):
        fallback_hits = _keyword_fallback_hits(
            input_message,
            top_k=top_k,
            filter_by=filter_by,
        )
        if fallback_hits:
            merged = _merge_hits(
                merged,
                fallback_hits,
                top_k=max(top_k, SETTINGS.retrieval_rerank_top_k),
                vector_weight=1.0,
                graph_weight=1.0,
            )
            provenance = "hybrid+keyword_fallback"
    if SETTINGS.retrieval_rerank_enabled:
        merged = _rerank_hits(input_message, merged, top_k=top_k)
    else:
        merged = merged[:top_k]
    return RetrievalResult(hits=merged, provenance=provenance)


def retrieve_top_similar(
    input_message: str,
    top_k: int = 5,
    filter_by: dict[str, str] | None = None,
    *,
    retrieval_mode: str | None = None,
) -> RetrievalResult:
    filter_mode = None
    if filter_by:
        filter_mode = filter_by.get(_POLICY_RETRIEVAL_MODE_KEY)
    mode = (filter_mode or retrieval_mode or SETTINGS.retrieval_mode).strip().lower()
    if mode == "hybrid":
        return retrieve_hybrid(input_message, top_k=top_k, filter_by=filter_by)
    candidate_k = max(top_k, SETTINGS.retrieval_rerank_top_k) if SETTINGS.retrieval_rerank_enabled else top_k
    vector_hits = _vector_hits(input_message, top_k=candidate_k, filter_by=filter_by)
    provenance = "vector"
    if SETTINGS.keyword_fallback_enabled and (
        not vector_hits or max(hit.score for hit in vector_hits) < SETTINGS.retrieval_min_score
    ):
        vector_hits = _keyword_fallback_hits(
            input_message,
            top_k=max(top_k, SETTINGS.retrieval_rerank_top_k) if SETTINGS.retrieval_rerank_enabled else top_k,
            filter_by=filter_by,
        )
        provenance = "keyword_fallback"
    if SETTINGS.retrieval_rerank_enabled:
        vector_hits = _rerank_hits(input_message, vector_hits, top_k=top_k)
    else:
        vector_hits = vector_hits[:top_k]
    return RetrievalResult(hits=vector_hits, provenance=provenance)
