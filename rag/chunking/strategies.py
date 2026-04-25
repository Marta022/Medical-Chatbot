"""Chunking strategy implementations used before embedding.

Purpose:
- Convert large text blocks into retrieval-friendly chunks.
- Preserve structural signals (headings/lists) where possible.

Available strategies:
- `section`: structure-aware grouping from markdown-like lines.
- `semantic`: strict LlamaIndex semantic splitter path.

`chunk_text(...)` is the strategy router for raw text.
`chunk_structured_chunks(...)` applies the same logic to `PdfStructuredChunk`
objects while preserving source metadata.
"""

from __future__ import annotations

import hashlib
import re

from models.contracts import PdfStructuredChunk
from rag.chunking.common import clean_line, is_bullet_item, is_markdown_heading, is_numbered_item

DEFAULT_STRATEGY = "section"
DEFAULT_SEMANTIC_MAX_CHARS = 700
SEMANTIC_SPLITTER_BUFFER_SIZE = 1
SEMANTIC_BREAKPOINT_PERCENTILE = 95
CHUNK_ID_ENCODING = "utf-8"


def section_chunks(text: str) -> list[str]:
    """Group text by markdown-like headings, lists, and paragraphs."""

    cleaned = text.strip()
    if not cleaned:
        return []
    return _group_lines_with_markdown_structure(cleaned)


def _is_list_item(line: str) -> bool:
    return is_numbered_item(line) or is_bullet_item(line)


def _is_markdown_heading(line: str) -> bool:
    return is_markdown_heading(line)


def _is_list_block(block: str) -> bool:
    """Return whether a block begins as a list structure."""

    lines = [line.strip() for line in block.splitlines() if line.strip()]
    return bool(lines and _is_list_item(lines[0]))


def _group_lines_with_markdown_structure(text: str) -> list[str]:
    """Collapse raw text lines into structure-aware chunk candidates."""

    blocks: list[str] = []
    paragraph: list[str] = []
    list_block: list[str] = []

    for raw_line in text.splitlines():
        line = clean_line(raw_line)
        if not line:
            if list_block:
                blocks.append("\n".join(list_block))
                list_block = []
            if paragraph:
                blocks.append(" ".join(paragraph))
                paragraph = []
            continue

        if _is_markdown_heading(line):
            if list_block:
                blocks.append("\n".join(list_block))
                list_block = []
            if paragraph:
                blocks.append(" ".join(paragraph))
                paragraph = []
            blocks.append(line)
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


def _llamaindex_semantic_chunks(text: str) -> list[str]:
    """Split text with the strict LlamaIndex semantic splitter."""

    try:
        from llama_index.core.node_parser import SemanticSplitterNodeParser
        from llama_index.core.schema import Document
    except Exception:
        return []

    try:
        parser = SemanticSplitterNodeParser.from_defaults(
            buffer_size=SEMANTIC_SPLITTER_BUFFER_SIZE,
            breakpoint_percentile_threshold=SEMANTIC_BREAKPOINT_PERCENTILE,
        )
        nodes = parser.get_nodes_from_documents([Document(text=text)])
    except Exception:
        return []

    chunks = [re.sub(r"\s+", " ", node.get_content()).strip() for node in nodes]
    return [chunk for chunk in chunks if chunk]


def semantic_chunks(
    text: str,
    *,
    max_chars: int = DEFAULT_SEMANTIC_MAX_CHARS,
    use_llamaindex: bool = True,
) -> list[str]:
    """Run strict semantic chunking after structure-aware preparation."""

    cleaned = text.strip()
    if not cleaned:
        return []
    blocks = _group_lines_with_markdown_structure(cleaned)
    if not blocks:
        return []
    prepared_text = "\n\n".join(blocks)

    if not use_llamaindex:
        raise RuntimeError("Semantic chunking requires llama-index semantic splitter.")
    semantic = _llamaindex_semantic_chunks(prepared_text)
    if not semantic:
        raise RuntimeError("Semantic chunking requires a working llama-index semantic splitter.")
    return semantic


def chunk_text(
    text: str,
    strategy: str = DEFAULT_STRATEGY,
    *,
    semantic_max_chars: int = DEFAULT_SEMANTIC_MAX_CHARS,
    semantic_use_llamaindex: bool = True,
) -> list[str]:
    """Dispatch one of the supported raw-text chunking strategies."""

    normalized = (strategy or DEFAULT_STRATEGY).strip().lower()
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
    """Build a stable chunk ID for rechunked structured content."""

    payload = (
        f"{base.source_file}|{base.page}|{base.chapter}|{base.section}|"
        f"{base.chunk_id}|{ordinal}|{text}"
    )
    return hashlib.sha1(payload.encode(CHUNK_ID_ENCODING)).hexdigest()[:16]


def chunk_structured_chunks(
    chunks: list[PdfStructuredChunk],
    strategy: str = "semantic",
    *,
    semantic_max_chars: int = DEFAULT_SEMANTIC_MAX_CHARS,
    semantic_use_llamaindex: bool = True,
) -> list[PdfStructuredChunk]:
    """Apply a chunking strategy while preserving structured chunk metadata."""

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
