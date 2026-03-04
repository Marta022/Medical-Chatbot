from __future__ import annotations

import hashlib
import re

from models.contracts import PdfStructuredChunk

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_NUMBERED_ITEM_PATTERN = re.compile(r"^\s*\d+[\.\)]\s+\S+")
_BULLET_ITEM_PATTERN = re.compile(r"^\s*[-*\u2022]\s+\S+")


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


def _is_list_item(line: str) -> bool:
    return bool(_NUMBERED_ITEM_PATTERN.match(line) or _BULLET_ITEM_PATTERN.match(line))


def _is_list_block(block: str) -> bool:
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    return bool(lines and _is_list_item(lines[0]))


def _group_lines_with_list_preservation(text: str) -> list[str]:
    blocks: list[str] = []
    paragraph: list[str] = []
    list_block: list[str] = []

    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            if list_block:
                blocks.append("\n".join(list_block))
                list_block = []
            if paragraph:
                blocks.append(" ".join(paragraph))
                paragraph = []
            continue

        if _is_list_item(line):
            if paragraph:
                blocks.append(" ".join(paragraph))
                paragraph = []
            list_block.append(line)
            continue

        if list_block:
            # Keep wrapped list descriptions attached to the active list block.
            if len(line.split()) <= 18 or line[:1].islower():
                list_block.append(line)
                continue
            blocks.append("\n".join(list_block))
            list_block = []

        paragraph.append(line)

    if list_block:
        blocks.append("\n".join(list_block))
    if paragraph:
        blocks.append(" ".join(paragraph))
    return blocks


def _merge_text_blocks(blocks: list[str], max_chars: int) -> list[str]:
    if not blocks:
        return []
    merged: list[str] = []
    current = ""
    for block in blocks:
        separator = "\n" if _is_list_block(block) else " "
        candidate = block if not current else f"{current}{separator}{block}"
        if len(candidate) <= max_chars or not current:
            current = candidate
            continue
        merged.append(current.strip())
        current = block
    if current:
        merged.append(current.strip())
    return [chunk for chunk in merged if chunk]


def _llamaindex_semantic_chunks(text: str) -> list[str]:
    try:
        from llama_index.core.node_parser import SemanticSplitterNodeParser
        from llama_index.core.schema import Document
    except Exception:
        return []

    try:
        parser = SemanticSplitterNodeParser.from_defaults(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
        )
        nodes = parser.get_nodes_from_documents([Document(text=text)])
    except Exception:
        return []

    chunks = [re.sub(r"\s+", " ", node.get_content()).strip() for node in nodes]
    return [chunk for chunk in chunks if chunk]


def semantic_chunks(
    text: str,
    *,
    max_chars: int = 700,
    use_llamaindex: bool = True,
) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    blocks = _group_lines_with_list_preservation(cleaned)
    if not blocks:
        return []
    prepared_text = "\n\n".join(blocks)

    if use_llamaindex:
        semantic = _llamaindex_semantic_chunks(prepared_text)
        if semantic:
            return semantic
    return _merge_text_blocks(blocks, max_chars=max_chars)


def chunk_text(
    text: str,
    strategy: str = "section",
    *,
    semantic_max_chars: int = 700,
    semantic_use_llamaindex: bool = True,
) -> list[str]:
    normalized = (strategy or "section").strip().lower()
    if normalized == "sentence":
        return sentence_chunks(text)
    if normalized == "window":
        return window_chunks(text)
    if normalized == "section":
        return section_chunks(text)
    if normalized == "semantic":
        return semantic_chunks(
            text,
            max_chars=semantic_max_chars,
            use_llamaindex=semantic_use_llamaindex,
        )
    raise ValueError(f"Unknown chunking strategy: {strategy}")


def _derive_semantic_chunk_id(base: PdfStructuredChunk, ordinal: int, text: str) -> str:
    payload = (
        f"{base.source_file}|{base.page}|{base.chapter}|{base.section}|"
        f"{base.chunk_id}|{ordinal}|{text}"
    )
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def chunk_structured_chunks(
    chunks: list[PdfStructuredChunk],
    strategy: str = "semantic",
    *,
    semantic_max_chars: int = 700,
    semantic_use_llamaindex: bool = True,
) -> list[PdfStructuredChunk]:
    rechunked: list[PdfStructuredChunk] = []
    for item in chunks:
        pieces = chunk_text(
            item.text,
            strategy=strategy,
            semantic_max_chars=semantic_max_chars,
            semantic_use_llamaindex=semantic_use_llamaindex,
        )
        if not pieces:
            continue

        for ordinal, piece in enumerate(pieces, start=1):
            normalized_piece = piece.strip()
            rechunked.append(
                PdfStructuredChunk(
                    source_file=item.source_file,
                    page=item.page,
                    chapter=item.chapter,
                    section=item.section,
                    chunk_id=_derive_semantic_chunk_id(item, ordinal, normalized_piece),
                    text=normalized_piece,
                    is_list=item.is_list or _is_list_block(normalized_piece),
                )
            )
    return rechunked
