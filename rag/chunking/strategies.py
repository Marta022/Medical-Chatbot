from __future__ import annotations

import re

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    parts = _SENTENCE_SPLIT.split(cleaned)
    return [part.strip() for part in parts if part.strip()]


def sentence_chunks(text: str, max_sentences: int = 3) -> list[str]:
    sentences = split_sentences(text)
    if not sentences:
        return []
    chunks: list[str] = []
    for idx in range(0, len(sentences), max_sentences):
        chunk = " ".join(sentences[idx : idx + max_sentences])
        chunks.append(chunk)
    return chunks


def window_chunks(text: str, window_size: int = 3, stride: int = 2) -> list[str]:
    sentences = split_sentences(text)
    if not sentences:
        return []
    chunks: list[str] = []
    for idx in range(0, len(sentences), stride):
        window = sentences[idx : idx + window_size]
        if not window:
            continue
        chunks.append(" ".join(window))
        if idx + window_size >= len(sentences):
            break
    return chunks


def section_chunks(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    return lines


def chunk_text(text: str, strategy: str = "section") -> list[str]:
    normalized = (strategy or "section").strip().lower()
    if normalized == "sentence":
        return sentence_chunks(text)
    if normalized == "window":
        return window_chunks(text)
    if normalized == "section":
        return section_chunks(text)
    raise ValueError(f"Unknown chunking strategy: {strategy}")
