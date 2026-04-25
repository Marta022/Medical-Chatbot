"""OpenAI chat completion client wrapper."""

from __future__ import annotations

import os

from openai import OpenAI

from config.settings import SETTINGS

_client: OpenAI | None = None
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"


def _get_client() -> OpenAI:
    """Return a lazily initialized OpenAI client."""

    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv(OPENAI_API_KEY_ENV))
    return _client


def openai_call(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    """Run a chat-completions request and return normalized text content."""

    chosen_model = model or SETTINGS.openai_model
    response = _get_client().chat.completions.create(
        model=chosen_model,
        messages=messages,
        temperature=temperature,
    )
    return (response.choices[0].message.content or "").strip()
