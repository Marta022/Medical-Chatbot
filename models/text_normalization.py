from __future__ import annotations

"""Shared text normalization utilities used across runtime modules."""

import unicodedata


def normalize_for_matching(text: str) -> str:
    """Normalize text for case/diacritic-insensitive matching."""

    normalized = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").strip()
