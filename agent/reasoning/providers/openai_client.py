from __future__ import annotations

import os

from openai import OpenAI

from config.settings import SETTINGS


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def openai_call(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    chosen_model = model or SETTINGS.openai_model
    response = _get_client().chat.completions.create(
        model=chosen_model,
        messages=messages,
        temperature=temperature,
    )
    return (response.choices[0].message.content or "").strip()

