"""Text normalization helpers for deterministic guardrail matching."""

from __future__ import annotations

from models.text_normalization import normalize_for_matching


def normalize_query(text: str) -> str:
    """Normalize user text once before all deterministic checks."""

    return normalize_for_matching(text)
