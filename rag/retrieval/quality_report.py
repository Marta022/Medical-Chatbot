from __future__ import annotations

from statistics import mean
from typing import Any

from agent.evaluation.benchmark import (
    DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
    load_retrieval_benchmark_queries,
)
from config.settings import SETTINGS
from models.contracts import PdfStructuredChunk
from rag.chunking.load_documents import load_pdf_chunks
from rag.retrieval.retriever import retrieve_top_similar

DEFAULT_PROBE_DATASET_JSON_PATH = DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH
SHORT_CHUNK_LT_20 = 20
SHORT_CHUNK_LT_40 = 40
DEFAULT_KEYWORD_LIMIT = 5
DEFAULT_TOP_K = 3


def _empty_chunk_metrics() -> dict[str, Any]:
    """Return the empty-state metrics payload for chunk analysis."""

    return {
        "count": 0,
        "avg_chars": 0,
        "short_lt_20_ratio": 0.0,
        "short_lt_40_ratio": 0.0,
    }


def _chunk_metrics(chunks: list[str]) -> dict[str, Any]:
    """Compute aggregate chunk-length metrics for a document."""

    if not chunks:
        return _empty_chunk_metrics()
    lengths = [len(chunk.strip()) for chunk in chunks if chunk.strip()]
    if not lengths:
        return _empty_chunk_metrics()
    short_20 = sum(1 for value in lengths if value < SHORT_CHUNK_LT_20)
    short_40 = sum(1 for value in lengths if value < SHORT_CHUNK_LT_40)
    return {
        "count": len(lengths),
        "avg_chars": round(mean(lengths), 2),
        "avg_words": round(mean(len(chunk.split()) for chunk in chunks if chunk.strip()), 2),
        "short_lt_20_ratio": round(short_20 / len(lengths), 4),
        "short_lt_40_ratio": round(short_40 / len(lengths), 4),
    }


def _retrieval_probe(query: str, top_k: int) -> dict[str, Any]:
    """Run one retrieval probe and normalize the report row."""

    try:
        result = retrieve_top_similar(query, top_k=top_k)
    except Exception as exc:
        return {"query": query, "error": str(exc), "hits": []}

    hits = [
        {
            "score": round(hit.score, 4),
            "source": hit.source,
            "source_file": hit.source_file,
            "page": hit.page,
            "section": hit.section,
            "chunk_id": hit.chunk_id,
            "text_preview": hit.text[:120],
        }
        for hit in result.hits
    ]
    return {
        "query": query,
        "hit_count": len(result.hits),
        "provenance": result.provenance,
        "hits": hits,
    }


def _chunk_keyword_probe(
    chunks: list[PdfStructuredChunk],
    keyword: str,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    """Find the top chunk matches for a keyword probe."""

    needle = keyword.strip().lower()
    if not needle:
        return []
    matches: list[dict[str, Any]] = []
    for chunk in chunks:
        haystack = chunk.text.lower()
        hit_count = haystack.count(needle)
        if hit_count <= 0:
            continue
        matches.append(
            {
                "source_file": chunk.source_file,
                "page": chunk.page,
                "chapter": chunk.chapter,
                "section": chunk.section,
                "chunk_id": chunk.chunk_id,
                "hit_count": hit_count,
                "text_preview": chunk.text[:160],
            }
        )
    matches = sorted(matches, key=lambda item: item["hit_count"], reverse=True)
    return matches[: max(limit, 1)]


def build_quality_report(
    *,
    pdf_paths: list[str],
    chunking_strategy: str,
    semantic_chunk_max_chars: int,
    semantic_use_llamaindex: bool,
    probe_queries: list[str] | None = None,
    probe_dataset_json_path: str = DEFAULT_PROBE_DATASET_JSON_PATH,
    keyword_queries: list[str] | None = None,
    keyword_limit: int = DEFAULT_KEYWORD_LIMIT,
    top_k: int = DEFAULT_TOP_K,
) -> dict[str, Any]:
    """Build a retrieval-quality report for configured PDFs and probe queries."""

    report: dict[str, Any] = {
        "chunking": {
            "strategy": chunking_strategy,
            "semantic_chunk_max_chars": semantic_chunk_max_chars,
            "semantic_use_llamaindex": semantic_use_llamaindex,
        },
        "pdf_chunk_metrics": {},
        "retrieval_probes": [],
        "chunk_keyword_probes": {},
    }

    for pdf_path in pdf_paths:
        chunks = load_pdf_chunks(
            pdf_path,
            chunking_strategy=chunking_strategy,
            semantic_chunk_max_chars=semantic_chunk_max_chars,
            semantic_use_llamaindex=semantic_use_llamaindex,
        )
        report["pdf_chunk_metrics"][pdf_path] = _chunk_metrics([chunk.text for chunk in chunks])
        if keyword_queries:
            report["chunk_keyword_probes"][pdf_path] = {
                query: _chunk_keyword_probe(chunks, query, limit=keyword_limit)
                for query in keyword_queries
            }

    active_queries = (
        probe_queries
        if probe_queries is not None
        else load_retrieval_benchmark_queries(probe_dataset_json_path)
    )
    report["retrieval_probes"] = [_retrieval_probe(query, top_k=top_k) for query in active_queries]
    report["retrieval_mode"] = SETTINGS.retrieval_mode
    return report
