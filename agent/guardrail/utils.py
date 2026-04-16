from __future__ import annotations

"""Shared deterministic matching helpers for guardrail logic."""


def find_matches(text: str, patterns: list[str]) -> list[str]:
    """Return deduplicated pattern matches found in `text` preserving declaration order."""

    seen: set[str] = set()
    matches: list[str] = []
    for pattern in patterns:
        if pattern in text and pattern not in seen:
            seen.add(pattern)
            matches.append(pattern)
    return matches


def find_grouped_matches(text: str, grouped_patterns: dict[str, list[str]]) -> list[str]:
    """Return deduplicated matches across grouped pattern definitions."""

    seen: set[str] = set()
    matches: list[str] = []
    for patterns in grouped_patterns.values():
        for pattern in patterns:
            if pattern in text and pattern not in seen:
                seen.add(pattern)
                matches.append(pattern)
    return matches


def has_any_match(text: str, patterns: list[str]) -> bool:
    """Return True when any pattern exists in text."""

    return any(pattern in text for pattern in patterns)
