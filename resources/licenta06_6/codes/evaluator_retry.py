"""Response quality evaluator with deterministic and adaptive retry outputs."""

from __future__ import annotations

from agent.evaluation.adaptive_prompt import build_adaptive_prompt
from agent.evaluation.failure_taxonomy import FailureType
from agent.evaluation.heuristics import run_heuristics
from config.eval_config import EVAL_CONFIG
from models import EvaluatorResult

BORDERLINE_FAILURE = FailureType.BORDERLINE
UNKNOWN_FAILURE = FailureType.UNKNOWN
SWITCH_LLM_FAILURES = {
    FailureType.UNSAFE_ADVICE,
    FailureType.HALLUCINATION_RISK,
}


def evaluate_response(
    query: str,
    response: str,
    context_lines: list[str] | None = None,
    use_llm_judge: bool | None = None,
    llm_judge_fn=None,
) -> EvaluatorResult:
    """Evaluate whether an answer is acceptable for final user delivery."""

    context_lines = context_lines or []
    issues = run_heuristics(query, response, context_lines)

    score = 1.0
    failure_types: list[FailureType] = []
    reasons: list[str] = []
    for failure_type, penalty in issues:
        score -= penalty
        failure_types.append(failure_type)
        reasons.append(failure_type.value)
    score = max(score, 0.0)

    judge_used = False
    use_judge = EVAL_CONFIG.use_llm_judge if use_llm_judge is None else use_llm_judge
    if (
        use_judge
        and llm_judge_fn is not None
        and EVAL_CONFIG.borderline_low <= score <= EVAL_CONFIG.borderline_high
    ):
        judge_score = float(llm_judge_fn(query, response, context_lines))
        score = (score + max(0.0, min(1.0, judge_score))) / 2.0
        judge_used = True
        if not failure_types:
            failure_types.append(BORDERLINE_FAILURE)
            reasons.append(BORDERLINE_FAILURE.value)

    passed = score >= EVAL_CONFIG.pass_score

    adaptive_prompt: str | None = None
    retry_strategy = "adjust_prompt"
    retry_recommended = not passed
    if not passed:
        primary_failure = failure_types[0] if failure_types else UNKNOWN_FAILURE
        adaptive_prompt = build_adaptive_prompt(
            failure_type=primary_failure,
            query=query,
            bad_response=response,
            context_lines=context_lines,
        )
        if any(failure in SWITCH_LLM_FAILURES for failure in failure_types):
            retry_strategy = "switch_llm"
        elif FailureType.REFUSED_WITH_CONTEXT in failure_types:
            # Do not pressure a medical model to answer after it reports insufficient support.
            retry_recommended = False

    return EvaluatorResult(
        passed=passed,
        score=round(score, 4),
        reasons=reasons,
        retry_recommended=retry_recommended,
        failure_types=failure_types,
        adaptive_prompt=adaptive_prompt,
        retry_strategy=retry_strategy,
        judge_used=judge_used,
    )
