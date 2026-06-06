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
