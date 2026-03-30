from __future__ import annotations

"""Anthropic provider placeholder for future integration."""

DEFAULT_ANTHROPIC_MODEL = "claude-3-haiku-20240307"


def anthropic_call(
    messages: list[dict[str, str]],
    model: str = DEFAULT_ANTHROPIC_MODEL,
    temperature: float = 0.0,
) -> str:
    """Raise until Anthropic wiring is implemented."""

    raise NotImplementedError(
        "Anthropic provider is not implemented yet. "
        "Use OPENAI or OLLAMA provider until this client is wired."
    )
