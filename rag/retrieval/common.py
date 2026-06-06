"""Shared helpers for retrieval payload normalization and scoring."""

from __future__ import annotations

import re

from models import RetrievalHit

TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
DEFAULT_RETRIEVAL_SOURCE = "unknown"
KEYWORD_FALLBACK_SOURCE = "keyword_fallback"
GRAPH_SOURCE = "graph"
MIN_TOKEN_LENGTH = 3


def build_retrieval_hit(
    *,
    score: float,
    payload: dict[str, object],
    source_override: str | None = None,
) -> RetrievalHit:
    """Build a normalized retrieval hit from a Qdrant-style payload."""

    source = source_override or str(payload.get("source", DEFAULT_RETRIEVAL_SOURCE))
    return RetrievalHit(
        title=str(payload.get("title", DEFAULT_RETRIEVAL_SOURCE)).strip(),
        text=str(payload.get("text", "")).strip(),
        score=float(score),
        source=source,
        source_file=(
            str(payload.get("source_file")) if payload.get("source_file") is not None else None
        ),
        page=int(payload.get("page")) if payload.get("page") is not None else None,
        section=str(payload.get("section")) if payload.get("section") is not None else None,
        chunk_id=str(payload.get("chunk_id")) if payload.get("chunk_id") is not None else None,
    )


def tokenize(text: str) -> set[str]:
    """Tokenize text into normalized retrieval terms."""

    return {
        token.lower()
        for token in TOKEN_PATTERN.findall(text or "")
        if len(token) >= MIN_TOKEN_LENGTH
    }
