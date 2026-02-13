from __future__ import annotations

from agent.reasoning.llm_router import llm_classify
from config.prompts import GUARDRAIL_SYSTEM_PROMPT


def classify_guardrail_with_llm(query: str) -> str:
    response = llm_classify(
        messages=[
            {"role": "system", "content": GUARDRAIL_SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ],
        temperature=0,
    )

    if not response:
        return "SAFE"

    label = response.strip().upper()
    if label in ("EMERGENCY", "UNSAFE", "SAFE"):
        return label

    if "EMERGENCY" in label:
        return "EMERGENCY"
    if "UNSAFE" in label:
        return "UNSAFE"
    return "SAFE"

