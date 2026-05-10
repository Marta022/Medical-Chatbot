"""OpenAI chat completion client wrapper."""

from __future__ import annotations

import os

from openai import OpenAI

from config.settings import SETTINGS

_client: OpenAI | None = None
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_API_BASE_URL_ENV = "OPENAI_API_BASE_URL"
OPENAI_BASE_URL_ENV = "OPENAI_BASE_URL"


def _model_supports_temperature(model: str) -> bool:
    """Return whether the OpenAI chat-completions call should send temperature."""

    normalized = model.strip().lower()
    return not normalized.startswith("gpt-5")


def _get_client() -> OpenAI:
    """Return a lazily initialized OpenAI client."""

    global _client
    if _client is None:
        base_url = os.getenv(OPENAI_API_BASE_URL_ENV) or os.getenv(OPENAI_BASE_URL_ENV)
        client_kwargs: dict[str, object] = {"api_key": os.getenv(OPENAI_API_KEY_ENV)}
        if base_url:
            client_kwargs["base_url"] = base_url
        _client = OpenAI(**client_kwargs)
    return _client


def openai_call(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    """Run a chat-completions request and return normalized text content."""

    chosen_model = model or SETTINGS.openai_model
    request_kwargs: dict[str, object] = {
        "model": chosen_model,
        "messages": messages,
    }
    if _model_supports_temperature(chosen_model):
        request_kwargs["temperature"] = temperature

    response = _get_client().chat.completions.create(**request_kwargs)
    return (response.choices[0].message.content or "").strip()
