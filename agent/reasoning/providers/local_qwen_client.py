from __future__ import annotations

from agent.reasoning.providers.local_gemma_client import ollama_call
from config.settings import SETTINGS


def qwen_call(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    chosen_model = model or SETTINGS.qwen_model
    return ollama_call(
        messages=messages,
        model=chosen_model,
        temperature=temperature,
    )
