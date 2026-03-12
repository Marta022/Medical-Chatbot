"""Qdrant ingestion pipeline.

What this module does:
- Builds vector points from two source families:
    1) structured tabular data (JSON/CSV medical items)
    2) corpus chunks (PDF/Markdown parsed as `PdfStructuredChunk`)
- Enriches PDF/Markdown chunks with detected entities.
- Optionally forwards chunk data to graph ingestion.
- Upserts points to Qdrant with batching + retry logic.

Design note:
- IDs are deterministic (`build_point_id`, `build_pdf_point_id`) so repeated ingest
    runs update existing points instead of creating uncontrolled duplicates.
"""

from __future__ import annotations

import hashlib
import logging
import time
import uuid

import httpx
from qdrant_client.http.exceptions import ResponseHandlingException
from qdrant_client.models import PointStruct

from knowledge.entities.extractor import extract_entities_from_chunk, load_disease_terms
from knowledge.graph.ingest import ingest_pdf_chunks_to_graph_safe
from knowledge.qdrant.client import COLLECTION, client, ensure_collection
from rag.chunking.load_documents import load_medical_items, load_pdf_chunks
from rag.chunking.strategies import chunk_text
from rag.retrieval.embeddings import embed_texts, vector_size


logger = logging.getLogger(__name__)


def _yield_batches(points: list[PointStruct], batch_size: int) -> list[list[PointStruct]]:
    if batch_size <= 0:
        raise ValueError("qdrant_upsert_batch_size must be greater than 0")
    return [points[index : index + batch_size] for index in range(0, len(points), batch_size)]


def _upsert_points_with_retry(
    points: list[PointStruct],
    *,
    batch_size: int,
    max_retries: int,
    retry_delay_seconds: float,
) -> None:
    if max_retries < 0:
        raise ValueError("qdrant_upsert_max_retries must be >= 0")
    if retry_delay_seconds < 0:
        raise ValueError("qdrant_upsert_retry_delay_seconds must be >= 0")

    batches = _yield_batches(points, batch_size)
    for batch_index, batch in enumerate(batches, start=1):
        for attempt in range(max_retries + 1):
            try:
                client.upsert(collection_name=COLLECTION, points=batch)
                break
            except (ResponseHandlingException, httpx.HTTPError) as exc:
                if attempt >= max_retries:
                    raise
                sleep_seconds = retry_delay_seconds * (2**attempt)
                logger.warning(
                    "Qdrant upsert transient failure (batch %s/%s, size=%s, attempt %s/%s): %s. Retrying in %.2fs.",
                    batch_index,
                    len(batches),
                    len(batch),
                    attempt + 1,
                    max_retries + 1,
                    exc,
                    sleep_seconds,
                )
                time.sleep(sleep_seconds)


def build_point_id(
    source: str,
    title: str,
    category: str | None,
    chunk_text_value: str,
    chunk_index: int,
) -> str:
    payload = f"{source}|{title}|{category or ''}|{chunk_index}|{chunk_text_value}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_URL, digest))


def build_pdf_point_id(
    source_file: str,
    page: int,
    chunk_id: str,
    text: str,
) -> str:
    payload = f"pdf|{source_file}|{page}|{chunk_id}|{text}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return str(uuid.uuid5(uuid.NAMESPACE_URL, digest))


def ingest(
    json_path: str,
    csv_path: str,
    chunking_strategy: str = "section",
    *,
    semantic_chunk_max_chars: int = 700,
    semantic_use_llamaindex: bool = True,
    pdf_paths: list[str] | None = None,
    include_structured_sources: bool = True,
    graph_ingest_enabled: bool = True,
    relation_min_confidence: float = 0.7,
    entity_min_confidence: float = 0.65,
    qdrant_upsert_batch_size: int = 128,
    qdrant_upsert_max_retries: int = 3,
    qdrant_upsert_retry_delay_seconds: float = 0.5,
    chunk_min_chars: int = 1,
    chunk_min_words: int = 1,
    list_chunk_min_words: int = 1,
) -> int:
    ensure_collection(vector_size())

    points: list[PointStruct] = []
    if include_structured_sources:
        items = load_medical_items(json_path, csv_path)
        for item in items:
            base_text = f"{item.title}\n{item.description}".strip()
            chunks = chunk_text(
                base_text,
                strategy=chunking_strategy,
                semantic_max_chars=semantic_chunk_max_chars,
                semantic_use_llamaindex=semantic_use_llamaindex,
            )
            if not chunks:
                chunks = [base_text]

            filtered_chunks = [
                chunk
                for chunk in chunks
                if _passes_chunk_quality(
                    chunk,
                    is_list=False,
                    min_chars=chunk_min_chars,
                    min_words=chunk_min_words,
                    list_min_words=list_chunk_min_words,
                )
            ]
            if not filtered_chunks:
                continue

            vectors = embed_texts(filtered_chunks)
            for chunk_index, (chunk, vector) in enumerate(
                zip(filtered_chunks, vectors, strict=False),
                start=1,
            ):
                payload = {
                    "text": chunk,
                    "title": item.title,
                    "source": item.source,
                    "category": item.category,
                    "chunk_index": chunk_index,
                    "chunking_strategy": chunking_strategy,
                    "semantic_chunk_max_chars": semantic_chunk_max_chars,
                    "semantic_use_llamaindex": semantic_use_llamaindex,
                }
                point_id = build_point_id(
                    item.source,
                    item.title,
                    item.category,
                    chunk,
                    chunk_index,
                )
                points.append(PointStruct(id=point_id, vector=vector, payload=payload))

    disease_terms = load_disease_terms(json_path)
    graph_chunks = []
    for pdf_path in (pdf_paths or []):
        pdf_chunks = load_pdf_chunks(
            pdf_path,
            chunking_strategy=chunking_strategy,
            semantic_chunk_max_chars=semantic_chunk_max_chars,
            semantic_use_llamaindex=semantic_use_llamaindex,
        )
        if not pdf_chunks:
            continue
        filtered_pdf_chunks = [
            chunk
            for chunk in pdf_chunks
            if _passes_chunk_quality(
                chunk.text,
                is_list=chunk.is_list,
                min_chars=chunk_min_chars,
                min_words=chunk_min_words,
                list_min_words=list_chunk_min_words,
            )
        ]
        if not filtered_pdf_chunks:
            continue
        graph_chunks.extend(filtered_pdf_chunks)

        vectors = embed_texts([chunk.text for chunk in filtered_pdf_chunks])
        for pdf_chunk, vector in zip(filtered_pdf_chunks, vectors, strict=False):
            entities = extract_entities_from_chunk(
                pdf_chunk,
                disease_terms=disease_terms,
                min_confidence=entity_min_confidence,
            )
            payload = {
                "text": pdf_chunk.text,
                "title": pdf_chunk.section,
                "source": "pdf",
                "source_file": pdf_chunk.source_file,
                "chapter": pdf_chunk.chapter,
                "section": pdf_chunk.section,
                "chunk_id": pdf_chunk.chunk_id,
                "is_list": pdf_chunk.is_list,
                "entities": [entity.to_dict() for entity in entities],
                "chunking_strategy": chunking_strategy,
                "semantic_chunk_max_chars": semantic_chunk_max_chars,
                "semantic_use_llamaindex": semantic_use_llamaindex,
            }
            point_id = build_pdf_point_id(
                pdf_chunk.source_file,
                pdf_chunk.page,
                pdf_chunk.chunk_id,
                pdf_chunk.text,
            )
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

    if graph_ingest_enabled and graph_chunks:
        ingest_pdf_chunks_to_graph_safe(
            graph_chunks,
            disease_terms=disease_terms,
            min_entity_confidence=entity_min_confidence,
            min_relation_confidence=relation_min_confidence,
        )

    _upsert_points_with_retry(
        points,
        batch_size=qdrant_upsert_batch_size,
        max_retries=qdrant_upsert_max_retries,
        retry_delay_seconds=qdrant_upsert_retry_delay_seconds,
    )
    return len(points)


def _passes_chunk_quality(
    text: str,
    *,
    is_list: bool,
    min_chars: int,
    min_words: int,
    list_min_words: int,
) -> bool:
    normalized = " ".join((text or "").split()).strip()
    if not normalized:
        return False
    words = len(normalized.split())
    if is_list:
        return words >= max(list_min_words, 1)
    return len(normalized) >= max(min_chars, 1) and words >= max(min_words, 1)
