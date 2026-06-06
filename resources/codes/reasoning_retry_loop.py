retrieval_result = self._deps.retrieve(
    request.query,
    request.top_k,
    retrieval_filters,
)

if not retrieval_result.hits or retrieval_result.max_score() < min_score:
    return ReasoningOutput(
        response=LOW_CONFIDENCE_MESSAGE,
        provider=None,
        model=None,
        retries=0,
        evaluator=None,
        retrieval=retrieval_result,
        context_lines=[],
    )

context_lines = retrieval_result.context_lines(with_score=True)
base_request = LLMRequest(
    system_prompt=self._system_prompt,
    user_message=request.query,
    context_block=build_context_block(context_lines),
)

for attempt in range(max_attempts):
    provider = self._select_provider(attempt, last_eval)
    attempt_request = self._apply_retry_guidance(base_request, last_eval)
    attempt_request.provider = provider

    last_response = self._deps.llm_call(attempt_request)
    last_eval = self._deps.evaluator(
        request.query,
        last_response.content,
        context_lines,
    )

    if last_eval.passed or not last_eval.retry_recommended:
        break
