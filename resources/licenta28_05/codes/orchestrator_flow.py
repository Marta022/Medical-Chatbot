def run(self, request: QueryRequest) -> OrchestratorResponse:
    """Run the full request lifecycle and return the final orchestrator response."""

    guardrail_result = self._deps.guardrail(request.query)
    if not guardrail_result.is_valid:
        return OrchestratorResponse(
            response=guardrail_result.message,
            provider=None,
            model=None,
            retries=0,
            guardrail=guardrail_result,
            evaluator=None,
            retrieval=None,
            context_lines=[],
        )

    reasoning_result = self._reasoning_engine.run(
        ReasoningInput(
            query=request.query,
            top_k=request.top_k,
            language=request.language,
            filters=request.filters,
        )
    )

    return OrchestratorResponse(
        response=reasoning_result.response,
        provider=reasoning_result.provider,
        model=reasoning_result.model,
        retries=reasoning_result.retries,
        guardrail=guardrail_result,
        evaluator=reasoning_result.evaluator,
        retrieval=reasoning_result.retrieval,
        context_lines=reasoning_result.context_lines,
    )
