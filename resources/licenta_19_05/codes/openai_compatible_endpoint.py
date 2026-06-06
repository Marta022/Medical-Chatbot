@app.post("/v1/chat/completions")
def openai_chat_completions() -> Any:
    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages", [])
    settings = _api_settings(app)
    if not isinstance(messages, list):
        raise ValueError("messages must be a list")
    if len(messages) > settings.max_messages:
        raise ValueError(f"too many messages (max {settings.max_messages})")

    query = _extract_user_message(messages)
    if len(query) > settings.max_query_chars:
        raise ValueError("query too long")
    query_request = QueryRequest(
        query=query,
        top_k=int(payload.get("top_k", SETTINGS.default_top_k)),
        language=str(payload.get("language", DEFAULT_CHAT_LANGUAGE)),
        filters=_build_retrieval_filters(payload),
    )
    if query_request.top_k > settings.max_top_k:
        raise ValueError(f"top_k must be <= {settings.max_top_k}")

    orchestrator = _deps(app).orchestrator_factory()
    result = orchestrator.run(query_request)
    _persist_interaction_safe(
        app,
        query_request=query_request,
        result=result,
        endpoint=request.path,
        session_id=_optional_session_id(payload),
    )

    completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created = int(time.time())
    model = str(payload.get("model") or result.model or _model_id())
    content = result.response or ""
    return jsonify(
        {
            "id": completion_id,
            "object": OPENAI_OBJECT_CHAT_COMPLETION,
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": OPENAI_ASSISTANT_ROLE, "content": content},
                    "finish_reason": OPENAI_FINISH_REASON_STOP,
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
    )
