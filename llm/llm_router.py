"""Router helpers for LLM completion, classification, and PDF markdown cleanup."""

from __future__ import annotations

from agent.reasoning.providers.anthropic_client import anthropic_call
from agent.reasoning.providers.local_gemma_client import ollama_call
from agent.reasoning.providers.local_qwen_client import qwen_call
from agent.reasoning.providers.openai_client import openai_call
from config.prompts import (
    PDF_MARKDOWN_CLEANUP_SYSTEM_PROMPT,
    build_pdf_markdown_cleanup_user_message,
)
from config.settings import SETTINGS
from models import LLMRequest, LLMResponse

PROVIDER_OPENAI = "openai"
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_OLLAMA = "ollama"
PROVIDER_QWEN = "qwen3.5"
SUPPORTED_PROVIDERS = {PROVIDER_OPENAI, PROVIDER_ANTHROPIC, PROVIDER_OLLAMA, PROVIDER_QWEN}
ERROR_UNSUPPORTED_PROVIDER = "Unsupported LLM provider: {provider}"
ERROR_INVALID_PAGE_NUMBER = "page_number must be greater than or equal to 1"
ERROR_EMPTY_PAGE_TEXT = "page_text must be a non-empty string"


def _select_provider(provider: str | None = None) -> str:
    """Resolve provider from request override or global settings."""

    chosen = (provider or SETTINGS.llm_provider).strip().lower()
    if chosen not in SUPPORTED_PROVIDERS:
        raise ValueError(ERROR_UNSUPPORTED_PROVIDER.format(provider=chosen))
    return chosen


def llm_ask(
    prompt: str,
    input_message: str,
    context_block: str,
    provider: str | None = None,
) -> str:
    """Run a chat request and return only response content."""

    request = LLMRequest(
        system_prompt=prompt,
        user_message=input_message,
        context_block=context_block,
        provider=provider,
    )
    return llm_ask_request(request).content


def llm_ask_request(request: LLMRequest) -> LLMResponse:
    """Route an LLMRequest to the configured provider and return envelope response."""

    provider = _select_provider(request.provider)
    if provider == PROVIDER_OLLAMA:
        content = ollama_call(messages=request.messages(), temperature=request.temperature)
        return LLMResponse(
            content=content,
            provider=PROVIDER_OLLAMA,
            model=SETTINGS.ollama_model,
        )
    if provider == PROVIDER_QWEN:
        content = qwen_call(messages=request.messages(), temperature=request.temperature)
        return LLMResponse(content=content, provider=PROVIDER_QWEN, model=SETTINGS.qwen_model)
    if provider == PROVIDER_ANTHROPIC:
        content = anthropic_call(messages=request.messages(), temperature=request.temperature)
        return LLMResponse(
            content=content,
            provider=PROVIDER_ANTHROPIC,
            model=SETTINGS.anthropic_model,
        )

    content = openai_call(messages=request.messages(), temperature=request.temperature)
    return LLMResponse(content=content, provider=PROVIDER_OPENAI, model=SETTINGS.openai_model)


def llm_classify(
    messages: list[dict[str, str]],
    temperature: float = 0.0,
    provider: str | None = None,
) -> str:
    """Classify input using the selected model provider."""

    chosen = _select_provider(provider)
    if chosen == PROVIDER_OLLAMA:
        return ollama_call(messages=messages, temperature=temperature)
    if chosen == PROVIDER_QWEN:
        return qwen_call(messages=messages, temperature=temperature)
    if chosen == PROVIDER_ANTHROPIC:
        return anthropic_call(messages=messages, temperature=temperature)
    return openai_call(messages=messages, temperature=temperature)


def llm_cleanup_pdf_page(
    *,
    source_file: str,
    page_number: int,
    page_text: str,
    provider: str | None = None,
) -> LLMResponse:
    """Convert one extracted PDF page to markdown-preserving cleaned text."""

    if page_number < 1:
        raise ValueError(ERROR_INVALID_PAGE_NUMBER)
    if not page_text or not page_text.strip():
        raise ValueError(ERROR_EMPTY_PAGE_TEXT)

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
