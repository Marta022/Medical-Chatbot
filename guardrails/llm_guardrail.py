# TODO(remove-shim): remove after P2 stabilization.
from agent.guardrail.llm_classifier import (
    GUARDRAIL_SYSTEM_PROMPT,
    classify_guardrail_with_llm,
)

__all__ = ["GUARDRAIL_SYSTEM_PROMPT", "classify_guardrail_with_llm"]
