from __future__ import annotations

from agent.reasoning.providers.local_gemma_client import ollama_call
from agent.reasoning.providers.local_qwen_client import qwen_call
from config.prompts import (
    PDF_MARKDOWN_CLEANUP_SYSTEM_PROMPT,
    build_pdf_markdown_cleanup_user_message,
)
from agent.reasoning.providers.openai_client import openai_call
from config.settings import SETTINGS
from models import LLMRequest, LLMResponse

SUPPORTED_PROVIDERS = {"openai", "ollama", "qwen3.5"}


def _select_provider(provider: str | None = None) -> str:
    chosen = (provider or SETTINGS.llm_provider).strip().lower()
    if chosen not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider: {chosen}")
    return chosen


def llm_ask(
    prompt: str,
    input_message: str,
    context_block: str,
    provider: str | None = None,
) -> str:
    request = LLMRequest(
        system_prompt=prompt,
        user_message=input_message,
        context_block=context_block,
        provider=provider,
    )
    return llm_ask_request(request).content


def llm_ask_request(request: LLMRequest) -> LLMResponse:
    provider = _select_provider(request.provider)
    if provider == "ollama":
        content = ollama_call(messages=request.messages(), temperature=request.temperature)
        return LLMResponse(content=content, provider="ollama", model=SETTINGS.ollama_model)
    if provider == "qwen3.5":
        content = qwen_call(messages=request.messages(), temperature=request.temperature)
        return LLMResponse(content=content, provider="qwen3.5", model=SETTINGS.qwen_model)

    content = openai_call(messages=request.messages(), temperature=request.temperature)
    return LLMResponse(content=content, provider="openai", model=SETTINGS.openai_model)


def llm_classify(
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    provider: str | None = None,
) -> str:
    chosen = _select_provider(provider)
    if chosen == "ollama":
        return ollama_call(messages=messages, temperature=temperature)
    if chosen == "qwen3.5":
        return qwen_call(messages=messages, temperature=temperature)
    return openai_call(messages=messages, temperature=temperature)


def llm_cleanup_pdf_page(
    *,
    source_file: str,
    page_number: int,
    page_text: str,
    provider: str | None = None,
) -> LLMResponse:
    if page_number < 1:
        raise ValueError("page_number must be greater than or equal to 1")
    if not page_text or not page_text.strip():
        raise ValueError("page_text must be a non-empty string")

    request = LLMRequest(
        system_prompt=PDF_MARKDOWN_CLEANUP_SYSTEM_PROMPT,
        user_message=build_pdf_markdown_cleanup_user_message(
            source_file=source_file,
            page_number=page_number,
            page_text=page_text,
        ),
        context_block="",
        temperature=0.0,
        provider=provider,
    )
    return llm_ask_request(request)
