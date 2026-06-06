def apply_guardrails(query: str) -> GuardrailResult:
    """Evaluate user query safety and return a structured guardrail result."""

    if not query or not query.strip():
        result = _base_result(
            category=CATEGORY_AMBIGUOUS,
            reason_code=REASON_EMPTY_QUERY,
            confidence=CONFIDENCE_EMPTY,
            is_valid=False,
        )
        result.message = EMPTY_QUERY_MESSAGE
        return result

    normalized_query = normalize_query(query)

    emergency_matches = find_grouped_matches(
        normalized_query,
        EMERGENCY_PATTERN_GROUPS,
    )
    if emergency_matches and not _is_educational_context(normalized_query):
        result = _base_result(
            category=CATEGORY_EMERGENCY,
            reason_code=REASON_KEYWORD_EMERGENCY,
            confidence=CONFIDENCE_KEYWORD_HIGH_RISK,
            is_valid=False,
        )
        result.is_emergency = True
        result.message = EMERGENCY_MESSAGE
        result.matched_keywords = emergency_matches
        return result

    critical_unsafe_matches = find_grouped_matches(
        normalized_query,
        UNSAFE_CRITICAL_PATTERN_GROUPS,
    )
    if critical_unsafe_matches:
        result = _base_result(
            category=CATEGORY_UNSAFE,
            reason_code=REASON_KEYWORD_UNSAFE_CRITICAL,
            confidence=CONFIDENCE_KEYWORD_HIGH_RISK,
            is_valid=False,
        )
        result.is_unsafe = True
        result.message = UNSAFE_CRITICAL_MESSAGE
        result.matched_keywords = critical_unsafe_matches
        return result
