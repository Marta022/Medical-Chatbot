def retrieve_top_similar(
    input_message: str,
    top_k: int = 5,
    filter_by: dict[str, str] | None = None,
    *,
    retrieval_mode: str | None = None,
) -> RetrievalResult:
    """Dispatch retrieval in vector or hybrid mode and apply fallback policy."""

    filter_mode = None
    if filter_by:
        filter_mode = filter_by.get(_POLICY_RETRIEVAL_MODE_KEY)
    mode = (filter_mode or retrieval_mode or SETTINGS.retrieval_mode).strip().lower()
    if mode == "hybrid":
        return retrieve_hybrid(input_message, top_k=top_k, filter_by=filter_by)
    candidate_k = (
        max(top_k, SETTINGS.retrieval_rerank_top_k) if SETTINGS.retrieval_rerank_enabled else top_k
    )
    vector_hits = _vector_hits(input_message, top_k=candidate_k, filter_by=filter_by)
    provenance = "vector"
    if SETTINGS.keyword_fallback_enabled and (
        not vector_hits or max(hit.score for hit in vector_hits) < SETTINGS.retrieval_min_score
    ):
        vector_hits = _keyword_fallback_hits(
            input_message,
            top_k=(
                max(top_k, SETTINGS.retrieval_rerank_top_k)
                if SETTINGS.retrieval_rerank_enabled
                else top_k
            ),
            filter_by=filter_by,
        )
        provenance = "keyword_fallback"
    if SETTINGS.retrieval_rerank_enabled:
        vector_hits = _rerank_hits(input_message, vector_hits, top_k=top_k)
    else:
        vector_hits = vector_hits[:top_k]
    return RetrievalResult(hits=vector_hits, provenance=provenance)
