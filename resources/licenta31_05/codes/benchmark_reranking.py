def _build_option_queries(item: dict[str, Any]) -> list[str]:
    """Build query pool containing base question and per-option probes."""

    question = item["intrebare"]
    queries = [question]
    for letter, value in item["choices"].items():
        cleaned = value.strip()
        if not cleaned:
            continue
        queries.append(f"{question}\nOptiunea {letter}: {cleaned}")
    return queries


def _rerank_benchmark_hits(
    item: dict[str, Any],
    hits: list[RetrievalHit],
    *,
    top_k: int,
) -> list[RetrievalHit]:
    """Rerank and deduplicate retrieval hits, preserving top-k high-signal chunks."""

    weighted = sorted(
        ((_benchmark_hit_relevance(item, hit), hit) for hit in hits),
        key=lambda pair: pair[0],
        reverse=True,
    )
    deduped: list[RetrievalHit] = []
    seen: set[tuple[str | None, int | None, str | None, str]] = set()
    for _score, hit in weighted:
        key = (hit.source_file, hit.page, hit.chunk_id, hit.text)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hit)
        if len(deduped) >= top_k:
            break
    return deduped
