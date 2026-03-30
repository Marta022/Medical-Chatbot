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

import logging
import time
from typing import Any

import httpx
from qdrant_client.http.exceptions import ResponseHandlingException
from qdrant_client.models import PointStruct

from knowledge.entities.extractor import extract_entities_from_chunk, load_disease_terms
from knowledge.graph.ingest import ingest_pdf_chunks_to_graph_safe
from knowledge.qdrant.client import COLLECTION, client, ensure_collection
from knowledge.qdrant.common import (
    PDF_SOURCE,
    build_pdf_payload,
    build_stable_point_id,
    build_structured_payload,
)
from rag.chunking.load_documents import load_medical_items, load_pdf_chunks
from rag.chunking.strategies import chunk_text
from rag.retrieval.embeddings import embed_texts, vector_size


logger = logging.getLogger(__name__)
DEFAULT_CHUNKING_STRATEGY = "section"
DEFAULT_SEMANTIC_CHUNK_MAX_CHARS = 700
DEFAULT_SEMANTIC_USE_LLAMAINDEX = True
DEFAULT_GRAPH_INGEST_ENABLED = True
DEFAULT_RELATION_MIN_CONFIDENCE = 0.7
DEFAULT_ENTITY_MIN_CONFIDENCE = 0.65
DEFAULT_QDRANT_UPSERT_BATCH_SIZE = 128
DEFAULT_QDRANT_UPSERT_MAX_RETRIES = 3
DEFAULT_QDRANT_UPSERT_RETRY_DELAY_SECONDS = 0.5
DEFAULT_CHUNK_MIN_CHARS = 1
DEFAULT_CHUNK_MIN_WORDS = 1
DEFAULT_LIST_CHUNK_MIN_WORDS = 1
MIN_QUALITY_THRESHOLD = 1


def _clamp_quality_threshold(value: int) -> int:
    """Normalize a chunk-quality threshold to a positive integer."""

    return max(value, MIN_QUALITY_THRESHOLD)


def _yield_batches(points: list[PointStruct], batch_size: int) -> list[list[PointStruct]]:
    """Split a point list into deterministic upsert batches."""

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
    """Upsert Qdrant points with exponential-backoff retry for transient failures."""

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
    """Build a deterministic point ID for a structured dataset chunk."""

    return build_stable_point_id(source, title, category or "", chunk_index, chunk_text_value)


def build_pdf_point_id(
    source_file: str,
    page: int,
    chunk_id: str,
    text: str,
) -> str:
    """Build a deterministic point ID for a PDF chunk."""

    return build_stable_point_id(PDF_SOURCE, source_file, page, chunk_id, text)


def _build_structured_point(
    *,
    item: Any,
    chunk: str,
    vector: list[float],
    chunk_index: int,
    chunking_strategy: str,
    semantic_chunk_max_chars: int,
    semantic_use_llamaindex: bool,
) -> PointStruct:
    """Create a Qdrant point for a structured source chunk."""

    payload = build_structured_payload(
        item,
        chunk=chunk,
        chunk_index=chunk_index,
        chunking_strategy=chunking_strategy,
        semantic_chunk_max_chars=semantic_chunk_max_chars,
        semantic_use_llamaindex=semantic_use_llamaindex,
    )
    point_id = build_point_id(item.source, item.title, item.category, chunk, chunk_index)
    return PointStruct(id=point_id, vector=vector, payload=payload)


def _build_pdf_point(
    *,
    pdf_chunk: Any,
    vector: list[float],
    entities: list[Any],
    chunking_strategy: str,
    semantic_chunk_max_chars: int,
    semantic_use_llamaindex: bool,
) -> PointStruct:
    """Create a Qdrant point for a PDF chunk."""

    payload = build_pdf_payload(
        pdf_chunk,
        entities=entities,
        chunking_strategy=chunking_strategy,
        semantic_chunk_max_chars=semantic_chunk_max_chars,
        semantic_use_llamaindex=semantic_use_llamaindex,
    )
    point_id = build_pdf_point_id(
        pdf_chunk.source_file,
        pdf_chunk.page,
        pdf_chunk.chunk_id,
        pdf_chunk.text,
    )
    return PointStruct(id=point_id, vector=vector, payload=payload)


def ingest(
    json_path: str,
    csv_path: str,
    chunking_strategy: str = DEFAULT_CHUNKING_STRATEGY,
    *,
    semantic_chunk_max_chars: int = DEFAULT_SEMANTIC_CHUNK_MAX_CHARS,
    semantic_use_llamaindex: bool = DEFAULT_SEMANTIC_USE_LLAMAINDEX,
    pdf_paths: list[str] | None = None,
    include_structured_sources: bool = True,
    graph_ingest_enabled: bool = DEFAULT_GRAPH_INGEST_ENABLED,
    relation_min_confidence: float = DEFAULT_RELATION_MIN_CONFIDENCE,
    entity_min_confidence: float = DEFAULT_ENTITY_MIN_CONFIDENCE,
    qdrant_upsert_batch_size: int = DEFAULT_QDRANT_UPSERT_BATCH_SIZE,
    qdrant_upsert_max_retries: int = DEFAULT_QDRANT_UPSERT_MAX_RETRIES,
    qdrant_upsert_retry_delay_seconds: float = DEFAULT_QDRANT_UPSERT_RETRY_DELAY_SECONDS,
    chunk_min_chars: int = DEFAULT_CHUNK_MIN_CHARS,
    chunk_min_words: int = DEFAULT_CHUNK_MIN_WORDS,
    list_chunk_min_words: int = DEFAULT_LIST_CHUNK_MIN_WORDS,
) -> int:
    """Ingest structured items and PDF chunks into Qdrant with stable IDs."""

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
                points.append(
                    _build_structured_point(
                        item=item,
                        chunk=chunk,
                        vector=vector,
                        chunk_index=chunk_index,
                        chunking_strategy=chunking_strategy,
                        semantic_chunk_max_chars=semantic_chunk_max_chars,
                        semantic_use_llamaindex=semantic_use_llamaindex,
                    )
                )

    disease_terms = load_disease_terms(json_path)
    graph_chunks: list[Any] = []
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
            points.append(
                _build_pdf_point(
                    pdf_chunk=pdf_chunk,
                    vector=vector,
                    entities=entities,
                    chunking_strategy=chunking_strategy,
                    semantic_chunk_max_chars=semantic_chunk_max_chars,
                    semantic_use_llamaindex=semantic_use_llamaindex,
                )
            )

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
    """Return whether a chunk meets the configured minimum information threshold."""

    normalized = " ".join((text or "").split()).strip()
    if not normalized:
        return False
    words = len(normalized.split())
    if is_list:
        return words >= _clamp_quality_threshold(list_min_words)
    return len(normalized) >= _clamp_quality_threshold(min_chars) and words >= _clamp_quality_threshold(
        min_words
    )
