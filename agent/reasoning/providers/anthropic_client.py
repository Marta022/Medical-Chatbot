from __future__ import annotations


def anthropic_call(
    messages: list[dict[str, str]],
    model: str = "claude-3-haiku-20240307",
    temperature: float = 0.0,
) -> str:
    raise NotImplementedError(
        "Anthropic provider is not implemented yet. "
        "Use OPENAI or OLLAMA provider until this client is wired."
    )
