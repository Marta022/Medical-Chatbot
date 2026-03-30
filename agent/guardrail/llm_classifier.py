from __future__ import annotations

"""LLM-backed fallback classification for guardrail decisioning."""

from agent.reasoning.llm_router import llm_classify
from config.prompts import GUARDRAIL_SYSTEM_PROMPT

LABEL_EMERGENCY = "EMERGENCY"
LABEL_UNSAFE = "UNSAFE"
LABEL_SAFE = "SAFE"
VALID_LABELS = (LABEL_EMERGENCY, LABEL_UNSAFE, LABEL_SAFE)


def classify_guardrail_with_llm(query: str) -> str:
    """Classify a query as SAFE, UNSAFE, or EMERGENCY using the active LLM provider."""

    response = llm_classify(
        messages=[
            {"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0,
    )

    if not response:
        return LABEL_SAFE

    label = response.strip().upper()
    if label in VALID_LABELS:
        return label

    if LABEL_EMERGENCY in label:
        return LABEL_EMERGENCY
    if LABEL_UNSAFE in label:
        return LABEL_UNSAFE
    return LABEL_SAFE
