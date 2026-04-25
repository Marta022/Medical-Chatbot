"""Core orchestrator for the medical chatbot request pipeline."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from agent.evaluation.evaluator import evaluate_response
from agent.guardrail.rules_engine import apply_guardrails
from agent.reasoning.engine import (
    ReasoningDependencies,
    ReasoningEngine,
    ReasoningInput,
)
from config.eval_config import EVAL_CONFIG, EvalConfig
from config.settings import BASE_SYSTEM_PROMPT
from llm.llm_router import llm_ask_request
from models import (
    EvaluatorResult,
    GuardrailResult,
    LLMRequest,
    LLMResponse,
    OrchestratorResponse,
    QueryRequest,
    RetrievalResult,
)
from rag.retrieval.retriever import retrieve_top_similar


@dataclass(frozen=True)
class OrchestratorDependencies:
    """Injected dependencies used by the orchestrator."""

    guardrail: Callable[[str], GuardrailResult] = apply_guardrails
    retrieve: Callable[[str, int, dict[str, str] | None], RetrievalResult] = retrieve_top_similar
    llm_call: Callable[[LLMRequest], LLMResponse] = llm_ask_request
    evaluator: Callable[[str, str, list[str] | None], EvaluatorResult] = evaluate_response


class Orchestrator:
    """Execute guardrails, retrieval, generation, and evaluation for one query."""

    def __init__(
        self,
        deps: OrchestratorDependencies | None = None,
        eval_config: EvalConfig | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._deps = deps or OrchestratorDependencies()
        self._eval_config = eval_config or EVAL_CONFIG
        self._system_prompt = system_prompt or BASE_SYSTEM_PROMPT
        self._reasoning_engine = ReasoningEngine(
            deps=ReasoningDependencies(
                retrieve=self._deps.retrieve,
                llm_call=self._deps.llm_call,
                evaluator=self._deps.evaluator,
            ),
            eval_config=self._eval_config,
            system_prompt=self._system_prompt,
        )

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
