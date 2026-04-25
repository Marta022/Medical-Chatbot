from __future__ import annotations

"""Deterministic-first and LLM-assisted guardrail policy engine."""

import logging

from config.settings import GUARDRAIL_LLM_ENABLED
from models import GuardrailResult

from agent.guardrail.llm_classifier import classify_guardrail_with_llm
from agent.guardrail.normalization import normalize_query
from agent.guardrail.patterns import (
    EDUCATIONAL_FRAMING_PATTERNS,
    EMERGENCY_PATTERN_GROUPS,
    FIRST_PERSON_SYMPTOM_MARKERS,
    SAFE_INFO_PATTERNS,
    UNSAFE_CRITICAL_PATTERN_GROUPS,
    UNSAFE_SOFT_PATTERN_GROUPS,
    URGENCY_MARKERS,
)
from agent.guardrail.policies import (
    AMBIGUOUS_MESSAGE,
    CATEGORY_AMBIGUOUS,
    CATEGORY_EMERGENCY,
    CATEGORY_INFO_ONLY,
    CATEGORY_PERSONAL_MEDICAL,
    CATEGORY_SAFE,
    CATEGORY_UNSAFE,
    CONFIDENCE_EMPTY,
    CONFIDENCE_KEYWORD_HIGH_RISK,
    CONFIDENCE_KEYWORD_SOFT_UNSAFE,
    CONFIDENCE_LLM,
    CONFIDENCE_LLM_UNAVAILABLE,
    CONFIDENCE_SAFE_DETERMINISTIC,
    EMPTY_QUERY_MESSAGE,
    EMERGENCY_MESSAGE,
    LABEL_AMBIGUOUS,
    LABEL_EMERGENCY,
    LABEL_UNSAFE,
    REASON_EMPTY_QUERY,
    REASON_KEYWORD_EMERGENCY,
    REASON_KEYWORD_INFO_ONLY,
    REASON_KEYWORD_PERSONAL_MEDICAL,
    REASON_KEYWORD_UNSAFE_CRITICAL,
    REASON_KEYWORD_UNSAFE_SOFT,
    REASON_LLM_AMBIGUOUS,
    REASON_LLM_EMERGENCY,
    REASON_LLM_UNAVAILABLE,
    REASON_LLM_UNSAFE,
    REASON_SAFE,
    UNSAFE_CRITICAL_MESSAGE,
    UNSAFE_SOFT_MESSAGE,
)
from agent.guardrail.utils import find_grouped_matches, has_any_match

logger = logging.getLogger(__name__)


def _base_result(
    *, category: str, reason_code: str, confidence: float, is_valid: bool
) -> GuardrailResult:
    """Construct a normalized guardrail result shell."""

    return GuardrailResult(
        category=category,
        reason_code=reason_code,
        confidence=confidence,
        is_valid=is_valid,
        matched_keywords=[],
        used_llm=False,
    )


def _log_decision(result: GuardrailResult, *, warning: bool = False) -> None:
    """Emit consistent structured logs for every guardrail decision."""

    payload = {
        "category": result.category,
        "reason_code": result.reason_code,
        "used_llm": result.used_llm,
        "matched_keywords": result.matched_keywords,
    }
    if warning:
        logger.warning("guardrail_decision", extra=payload)
        return
    logger.info("guardrail_decision", extra=payload)


def _is_educational_context(normalized_query: str) -> bool:
    """Return True when query appears to be educational and not urgent/personal."""

    has_educational_signal = has_any_match(normalized_query, EDUCATIONAL_FRAMING_PATTERNS)
    has_personal_symptoms = has_any_match(normalized_query, FIRST_PERSON_SYMPTOM_MARKERS)
    has_urgency_signal = has_any_match(normalized_query, URGENCY_MARKERS)
    return has_educational_signal and not has_personal_symptoms and not has_urgency_signal


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

    should_use_llm = GUARDRAIL_LLM_ENABLED and (is_personal_medical or not is_info_only)
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
            )
            result.used_llm = True
            result.matched_keywords = find_grouped_matches(
                normalized_query,
                {"personal": FIRST_PERSON_SYMPTOM_MARKERS},
            )
            _log_decision(result)
            return result

    if is_personal_medical:
        result = _base_result(
            category=CATEGORY_PERSONAL_MEDICAL,
            reason_code=REASON_KEYWORD_PERSONAL_MEDICAL,
            confidence=CONFIDENCE_SAFE_DETERMINISTIC,
            is_valid=True,
        )
        result.matched_keywords = find_grouped_matches(
            normalized_query,
            {"personal": FIRST_PERSON_SYMPTOM_MARKERS},
        )
        _log_decision(result)
        return result

    result = _base_result(
        category=CATEGORY_SAFE,
        reason_code=REASON_SAFE,
        confidence=CONFIDENCE_SAFE_DETERMINISTIC,
        is_valid=True,
    )
    _log_decision(result)
    return result
