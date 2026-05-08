"""Shared helpers for Qdrant ingestion and collection management."""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from models import MedicalEntity, MedicalItem, PdfStructuredChunk

PDF_SOURCE = "pdf"
POINT_ID_NAMESPACE = uuid.NAMESPACE_URL
POINT_ID_HASH_ENCODING = "utf-8"


def build_stable_point_id(*parts: object) -> str:
    """Create a deterministic UUID from a sequence of identity parts."""

    payload = "|".join(str(part) for part in parts)
    digest = hashlib.sha256(payload.encode(POINT_ID_HASH_ENCODING)).hexdigest()
    return str(uuid.uuid5(POINT_ID_NAMESPACE, digest))


def build_structured_payload(
    item: MedicalItem,
    *,
    chunk: str,
    chunk_index: int,
    chunking_strategy: str,
    semantic_chunk_max_chars: int,
    semantic_use_llamaindex: bool,
) -> dict[str, Any]:
    """Build the Qdrant payload for a structured dataset chunk."""

    return {
        "text": chunk,
        "title": item.title,
        "source": item.source,
        "category": item.category,
        "chunk_index": chunk_index,
        "chunking_strategy": chunking_strategy,
        "semantic_chunk_max_chars": semantic_chunk_max_chars,
        "semantic_use_llamaindex": semantic_use_llamaindex,
    }


def build_pdf_payload(
    chunk: PdfStructuredChunk,
    *,
    entities: list[MedicalEntity],
    chunking_strategy: str,
    semantic_chunk_max_chars: int,
    semantic_use_llamaindex: bool,
) -> dict[str, Any]:
    """Build the Qdrant payload for a PDF chunk and its extracted entities."""

    return {
        "text": chunk.text,
        "title": chunk.section,
        "source": PDF_SOURCE,
        "source_file": chunk.source_file,
        "chapter": chunk.chapter,
        "section": chunk.section,
        "chunk_id": chunk.chunk_id,
        "is_list": chunk.is_list,
        "entities": [entity.to_dict() for entity in entities],
        "chunking_strategy": chunking_strategy,
        "semantic_chunk_max_chars": semantic_chunk_max_chars,
        "semantic_use_llamaindex": semantic_use_llamaindex,
    }
