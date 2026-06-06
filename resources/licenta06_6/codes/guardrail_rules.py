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
        _log_decision(result)
        return result

    normalized_query = normalize_query(query)

    emergency_matches = find_grouped_matches(normalized_query, EMERGENCY_PATTERN_GROUPS)
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
        _log_decision(result, warning=True)
        return result

    critical_unsafe_matches = find_grouped_matches(normalized_query, UNSAFE_CRITICAL_PATTERN_GROUPS)
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
        _log_decision(result, warning=True)
        return result

    soft_unsafe_matches = find_grouped_matches(normalized_query, UNSAFE_SOFT_PATTERN_GROUPS)
    if soft_unsafe_matches:
        result = _base_result(
            category=CATEGORY_UNSAFE,
            reason_code=REASON_KEYWORD_UNSAFE_SOFT,
            confidence=CONFIDENCE_KEYWORD_SOFT_UNSAFE,
            is_valid=False,
        )
        result.is_unsafe = True
        result.message = UNSAFE_SOFT_MESSAGE
        result.matched_keywords = soft_unsafe_matches
        _log_decision(result, warning=True)
        return result

    is_personal_medical = has_any_match(normalized_query, FIRST_PERSON_SYMPTOM_MARKERS)
    is_info_only = has_any_match(normalized_query, SAFE_INFO_PATTERNS) and not is_personal_medical

    if is_info_only:
        result = _base_result(
            category=CATEGORY_INFO_ONLY,
            reason_code=REASON_KEYWORD_INFO_ONLY,
            confidence=CONFIDENCE_SAFE_DETERMINISTIC,
            is_valid=True,
        )
        _log_decision(result)
        return result

    should_use_llm = GUARDRAIL_LLM_ENABLED and is_personal_medical
    if should_use_llm:
        try:
            label = classify_guardrail_with_llm(query)
        except Exception as exc:
            logger.exception("guardrail_llm_unavailable", extra={"error": str(exc)})
            result = _base_result(
                category=CATEGORY_SAFE,
                reason_code=REASON_LLM_UNAVAILABLE,
                confidence=CONFIDENCE_LLM_UNAVAILABLE,
                is_valid=True,
            )
            _log_decision(result)
            return result

        if label == LABEL_EMERGENCY:
            result = _base_result(
                category=CATEGORY_EMERGENCY,
                reason_code=REASON_LLM_EMERGENCY,
                confidence=CONFIDENCE_LLM,
                is_valid=False,
            )
            result.is_emergency = True
            result.message = EMERGENCY_MESSAGE
            result.used_llm = True
            _log_decision(result, warning=True)
            return result

        if label == LABEL_UNSAFE:
            result = _base_result(
                category=CATEGORY_UNSAFE,
                reason_code=REASON_LLM_UNSAFE,
                confidence=CONFIDENCE_LLM,
                is_valid=False,
            )
            result.is_unsafe = True
            result.message = UNSAFE_CRITICAL_MESSAGE
            result.used_llm = True
            _log_decision(result, warning=True)
            return result

        if label == LABEL_AMBIGUOUS:
            result = _base_result(
                category=CATEGORY_AMBIGUOUS,
                reason_code=REASON_LLM_AMBIGUOUS,
                confidence=CONFIDENCE_LLM,
                is_valid=False,
            )
            result.message = AMBIGUOUS_MESSAGE
            result.used_llm = True
            _log_decision(result, warning=True)
            return result

        if is_personal_medical:
            result = _base_result(
                category=CATEGORY_PERSONAL_MEDICAL,
                reason_code=REASON_KEYWORD_PERSONAL_MEDICAL,
                confidence=CONFIDENCE_LLM,
                is_valid=True,
