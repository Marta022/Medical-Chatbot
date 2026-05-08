"""Shared helpers for the orchestrator package."""

from __future__ import annotations

from typing import TypedDict

from models import LLMRequest


class CitationRow(TypedDict):
    """Normalized citation metadata for a retrieved chunk."""

    source_file: str
    page: int
    section: str
    chunk_id: str


def clone_llm_request(base_request: LLMRequest, *, user_message: str | None = None) -> LLMRequest:
    """Create a shallow copy of an LLM request with optional message override.

    Args:
        base_request: Source request to copy.
        user_message: Replacement user message when retry guidance is applied.

    Returns:
        A copied request safe to mutate per attempt.
    """

    return LLMRequest(
        system_prompt=base_request.system_prompt,
        user_message=user_message if user_message is not None else base_request.user_message,
        context_block=base_request.context_block,
        temperature=base_request.temperature,
        provider=base_request.provider,
    )
