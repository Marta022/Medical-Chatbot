from __future__ import annotations

from models import EvaluatorResult


def evaluate_response(
    query: str,
    response: str,
    context_lines: list[str] | None = None,
) -> EvaluatorResult:
    context_lines = context_lines or []
    reasons: list[str] = []

    if not response or not response.strip():
        reasons.append("empty_response")
        return EvaluatorResult(passed=False, score=0.0, reasons=reasons, retry_recommended=True)

    score = 1.0
    if len(response.strip()) < 10:
        reasons.append("response_too_short")
        score -= 0.2

    if context_lines and "I don't know based on the available data." in response:
        reasons.append("context_available_but_unknown_answer")
        score -= 0.3

    passed = score >= 0.7
    return EvaluatorResult(
        passed=passed,
        score=max(score, 0.0),
        reasons=reasons,
        retry_recommended=not passed,
    )

