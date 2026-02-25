# TODO(remove-shim): remove after P2 stabilization.
from agent.guardrail.rules_engine import apply_guardrails as _apply_guardrails


def apply_guardrails(query: str) -> dict[str, object]:
    return _apply_guardrails(query).to_dict()
