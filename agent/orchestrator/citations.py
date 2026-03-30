"""Citation and retrieval evidence formatting helpers."""

from __future__ import annotations

from agent.orchestrator.common import CitationRow
from models import RetrievalHit, RetrievalResult

DEFAULT_SOURCE_FILE = "unknown"
DEFAULT_PAGE = -1
DEFAULT_SECTION = "unknown"
DEFAULT_CHUNK_ID = "unknown"
ELLIPSIS_SUFFIX = "..."
RETRIEVED_CHUNKS_HEADER = "Most similar chunks:"
CITATIONS_HEADER = "Citations:"


def _normalize_hit_metadata(hit: RetrievalHit) -> CitationRow:
    """Build a normalized citation row from a retrieval hit."""

    return CitationRow(
        source_file=hit.source_file or hit.source or DEFAULT_SOURCE_FILE,
        page=hit.page if hit.page is not None else DEFAULT_PAGE,
        section=hit.section or DEFAULT_SECTION,
        chunk_id=hit.chunk_id or DEFAULT_CHUNK_ID,
    )


def append_retrieved_chunks_block(
    response: str,
    retrieval_result: RetrievalResult,
    *,
    max_chunks: int = 3,
    max_text_chars: int = 280,
) -> str:
    """Append a short retrieved-chunks block to a generated response."""

    if not retrieval_result.hits or max_chunks <= 0:
        return response

    lines = [response.rstrip(), "", RETRIEVED_CHUNKS_HEADER]
    for index, hit in enumerate(retrieval_result.hits[:max_chunks], start=1):
        metadata = _normalize_hit_metadata(hit)
        text = hit.text.strip()
        if len(text) > max_text_chars:
            text = text[: max_text_chars - len(ELLIPSIS_SUFFIX)].rstrip() + ELLIPSIS_SUFFIX
        lines.append(
            (
                f"[{index}] score={hit.score:.4f}; "
                f"source_file={metadata['source_file']}; "
                f"page={metadata['page']}; "
                f"section={metadata['section']}; "
                f"chunk_id={metadata['chunk_id']}; "
                f"text={text}"
            )
        )
    return "\n".join(lines).strip()


def build_citation_rows(
    retrieval_result: RetrievalResult,
    *,
    max_citations: int = 5,
) -> list[CitationRow]:
    """Collect unique citation rows from retrieval hits."""

    rows: list[CitationRow] = []
    seen: set[tuple[str, int, str, str]] = set()

    for hit in retrieval_result.hits:
        row = _normalize_hit_metadata(hit)
        key = (row["source_file"], row["page"], row["section"], row["chunk_id"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
        if len(rows) >= max_citations:
            break
    return rows


def append_citation_block(response: str, citations: list[CitationRow]) -> str:
    """Append structured citations to a response."""

    if not citations:
        return response
    lines = [response.rstrip(), "", CITATIONS_HEADER]
    for index, item in enumerate(citations, start=1):
        lines.append(
            (
                f"[{index}] source_file={item['source_file']}; "
                f"page={item['page']}; "
                f"section={item['section']}; "
                f"chunk_id={item['chunk_id']}"
            )
        )
    return "\n".join(lines).strip()
