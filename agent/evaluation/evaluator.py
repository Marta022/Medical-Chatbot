from __future__ import annotations

"""Response quality evaluator with deterministic acceptance heuristics."""

from config.eval_config import EVAL_CONFIG
from models import EvaluatorResult

MIN_RESPONSE_LENGTH = 10
UNKNOWN_WITH_CONTEXT_RESPONSE = "I don't know based on the available data."
REASON_EMPTY_RESPONSE = "empty_response"
REASON_RESPONSE_TOO_SHORT = "response_too_short"
REASON_CONTEXT_AVAILABLE_BUT_UNKNOWN = "context_available_but_unknown_answer"
SHORT_RESPONSE_PENALTY = 0.2
UNKNOWN_WITH_CONTEXT_PENALTY = 0.3


def evaluate_response(
    query: str,
    response: str,
    context_lines: list[str] | None = None,
) -> EvaluatorResult:
    """Evaluate whether an answer is acceptable for final user delivery."""

    context_lines = context_lines or []
    reasons: list[str] = []

    if not response or not response.strip():
        reasons.append(REASON_EMPTY_RESPONSE)
        return EvaluatorResult(passed=False, score=0.0, reasons=reasons, retry_recommended=True)

    score = 1.0
    if len(response.strip()) < MIN_RESPONSE_LENGTH:
        reasons.append(REASON_RESPONSE_TOO_SHORT)
        score -= SHORT_RESPONSE_PENALTY

    if context_lines and UNKNOWN_WITH_CONTEXT_RESPONSE in response:
        reasons.append(REASON_CONTEXT_AVAILABLE_BUT_UNKNOWN)
        score -= UNKNOWN_WITH_CONTEXT_PENALTY

    passed = score >= EVAL_CONFIG.pass_score
    return EvaluatorResult(
        passed=passed,
        score=max(score, 0.0),
        reasons=reasons,
        retry_recommended=not passed,
    )
