from __future__ import annotations

"""Adaptive retry prompt templates driven by evaluator failure type."""

from agent.evaluation.failure_taxonomy import FailureType

CONTEXT_SUMMARY_MAX_CHARS = 800
BAD_RESPONSE_MAX_CHARS = 500
CONTEXT_SUMMARY_MAX_LINES = 5

_TEMPLATES: dict[FailureType, str] = {
    FailureType.EMPTY: (
        "Your previous response was empty. Answer the question using the available context.\n"
        "Question: {query}"
    ),
    FailureType.TOO_SHORT: (
        "Your previous response was too brief for a medical question. "
        "Provide a complete answer in at least 2-3 sentences and include a safety caveat when needed.\n"
        "Question: {query}"
    ),
    FailureType.REFUSED_WITH_CONTEXT: (
        "You refused to answer although context exists. Use the context below and answer directly.\n"
        "Context:\n{context_summary}\n"
        "Question: {query}"
    ),
    FailureType.CONTEXT_IGNORED: (
        "Your answer did not use the retrieved context. Revise the answer using this context:\n"
        "{context_summary}\n"
        "Question: {query}"
    ),
    FailureType.UNSAFE_ADVICE: (
        "Your answer included potentially unsafe dosage guidance without a caution. "
        "Revise with explicit medical safety language and a recommendation to consult a clinician.\n"
        "Question: {query}\n"
        "Previous response: {bad_response}"
    ),
    FailureType.HALLUCINATION_RISK: (
        "Your answer may include unsupported claims. Keep only statements grounded in the provided context.\n"
        "Context:\n{context_summary}\n"
        "Question: {query}"
    ),
    FailureType.INCOMPLETE: (
        "Your previous answer appears incomplete. Provide a complete final answer.\n"
        "Question: {query}\n"
        "Previous response: {bad_response}"
    ),
    FailureType.OFF_TOPIC: (
        "Your previous answer was off topic. Focus only on this question:\n"
        "{query}"
    ),
    FailureType.BORDERLINE: (
        "Improve this answer for accuracy, completeness, and safety.\n"
        "Question: {query}\n"
        "Draft response: {bad_response}\n"
        "Context:\n{context_summary}"
    ),
    FailureType.UNKNOWN: (
        "Provide a clearer and safer answer grounded in available context.\n"
        "Question: {query}"
    ),
}


def build_adaptive_prompt(
    failure_type: FailureType,
    query: str,
    bad_response: str,
    context_lines: list[str],
) -> str:
    """Build targeted retry instruction from failure type."""

    template = _TEMPLATES.get(failure_type, _TEMPLATES[FailureType.UNKNOWN])
    context_summary = "No context available."
    if context_lines:
        context_summary = "\n".join(context_lines[:CONTEXT_SUMMARY_MAX_LINES])

    return template.format(
        query=query.strip(),
        bad_response=bad_response.strip()[:BAD_RESPONSE_MAX_CHARS],
        context_summary=context_summary[:CONTEXT_SUMMARY_MAX_CHARS],
    )
