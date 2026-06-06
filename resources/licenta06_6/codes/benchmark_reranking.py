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


def _benchmark_hit_relevance(item: dict[str, Any], hit: RetrievalHit) -> float:
    """Score benchmark retrieval hits using query and option overlap signals."""

    question_tokens = _tokenize(item["intrebare"])
    hit_text = f"{hit.title} {hit.text} {hit.section or ''}"
    hit_tokens = _tokenize(hit_text)
    if not question_tokens or not hit_tokens:
        return hit.score

    overlap = len(question_tokens.intersection(hit_tokens)) / max(len(question_tokens), 1)
    option_bonus = 0.0
    compact_hit = _compact_pattern(hit_text)
    for value in item["choices"].values():
        compact_option = _compact_pattern(value)
        if compact_option and compact_option in compact_hit:
            option_bonus = max(option_bonus, 1.0)

        option_tokens = _tokenize(value)
        if not option_tokens:
            continue
        option_overlap = len(option_tokens.intersection(hit_tokens)) / max(len(option_tokens), 1)
        option_bonus = max(option_bonus, option_overlap)
    if _benchmark_requires_single_answer(item) and _choice_pattern_implies_single_answer(
        item["choices"]
    ):
        return (hit.score * 0.45) + (overlap * 0.2) + (option_bonus * 0.35)
    return (hit.score * 0.65) + (overlap * 0.2) + (option_bonus * 0.15)


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
