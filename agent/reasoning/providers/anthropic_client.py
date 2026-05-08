"""Anthropic chat client wrapper."""

from __future__ import annotations

import os

from anthropic import Anthropic

from config.settings import SETTINGS

DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-latest"
ANTHROPIC_API_KEY_ENV = "ANTHROPIC_API_KEY"
_client: Anthropic | None = None


def _get_client() -> Anthropic:
    """Return lazily initialized Anthropic client."""

    global _client
    if _client is None:
        _client = Anthropic(api_key=os.getenv(ANTHROPIC_API_KEY_ENV))
    return _client


def _merge_messages(messages: list[dict[str, str]]) -> str:
    """Flatten chat messages into one user payload for Anthropic messages API."""

    parts: list[str] = []
    for message in messages:
        role = str(message.get("role", "user")).strip().lower()
        content = str(message.get("content", "")).strip()
        if not content:
            continue
        if role == "system":
            parts.append(f"[SYSTEM]\n{content}")
        elif role == "assistant":
            parts.append(f"[ASSISTANT]\n{content}")
        else:
            parts.append(f"[USER]\n{content}")
    return "\n\n".join(parts)


def anthropic_call(
    messages: list[dict[str, str]],
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    """Run an Anthropic messages request and return normalized text content."""

    chosen_model = model or SETTINGS.anthropic_model
    merged_prompt = _merge_messages(messages)
    response = _get_client().messages.create(
        model=chosen_model,
        max_tokens=1024,
        temperature=temperature,
        messages=[{"role": "user", "content": merged_prompt}],
    )
    parts: list[str] = []
    for block in response.content:
        block_text = getattr(block, "text", "")
        if block_text:
            parts.append(block_text)
    return "\n".join(parts).strip()
