"""Ollama provider wrapper for local model inference."""

from __future__ import annotations

from config.settings import SETTINGS

try:
    import ollama
except ImportError:  # pragma: no cover - optional dependency
    ollama = None


def ollama_call(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    """Run a local Ollama chat request and return stripped text content."""

    if ollama is None:
        raise RuntimeError("ollama package is not installed")

    chosen_model = model or SETTINGS.ollama_model
    response = ollama.chat(
        model=chosen_model,
        messages=messages,
        options={"temperature": temperature},
    )
    return response["message"]["content"].strip()
