from __future__ import annotations

from models import RetrievalResult


def append_retrieved_chunks_block(
    response: str,
    retrieval_result: RetrievalResult,
    *,
    max_chunks: int = 3,
    max_text_chars: int = 280,
) -> str:
    if not retrieval_result.hits or max_chunks <= 0:
        return response

    lines = [response.rstrip(), "", "Most similar chunks:"]
    for index, hit in enumerate(retrieval_result.hits[:max_chunks], start=1):
        source_file = hit.source_file or hit.source or "unknown"
        page = hit.page if hit.page is not None else -1
        section = hit.section or "unknown"
        chunk_id = hit.chunk_id or "unknown"
        text = hit.text.strip()
        if len(text) > max_text_chars:
            text = text[: max_text_chars - 3].rstrip() + "..."
        lines.append(
            (
                f"[{index}] score={hit.score:.4f}; "
                f"source_file={source_file}; "
                f"page={page}; "
                f"section={section}; "
                f"chunk_id={chunk_id}; "
                f"text={text}"
            )
        )
    return "\n".join(lines).strip()


def build_citation_rows(
    retrieval_result: RetrievalResult,
    *,
    max_citations: int = 5,
) -> list[dict[str, str | int]]:
    rows: list[dict[str, str | int]] = []
    seen: set[tuple[str, int, str, str]] = set()

    for hit in retrieval_result.hits:
        source_file = hit.source_file or hit.source or "unknown"
        page = hit.page if hit.page is not None else -1
        section = hit.section or "unknown"
        chunk_id = hit.chunk_id or "unknown"
        key = (source_file, int(page), section, chunk_id)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "source_file": source_file,
                "page": int(page),
                "section": section,
                "chunk_id": chunk_id,
            }
        )
        if len(rows) >= max_citations:
            break
    return rows


def append_citation_block(response: str, citations: list[dict[str, str | int]]) -> str:
    if not citations:
        return response
    lines = [response.rstrip(), "", "Citations:"]
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
