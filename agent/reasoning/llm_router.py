from __future__ import annotations

from config.settings import SETTINGS
from models import LLMRequest, LLMResponse

from agent.reasoning.providers.local_gemma_client import ollama_call
from agent.reasoning.providers.openai_client import openai_call

SUPPORTED_PROVIDERS = {"openai", "ollama"}


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
    return openai_call(messages=messages, temperature=temperature)

