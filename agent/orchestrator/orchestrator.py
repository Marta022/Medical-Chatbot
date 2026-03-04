from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from agent.evaluation.evaluator import evaluate_response
from agent.guardrail.rules_engine import apply_guardrails
from agent.orchestrator.citations import (
    append_citation_block,
    append_retrieved_chunks_block,
    build_citation_rows,
)
from agent.reasoning.llm_router import llm_ask_request
from agent.reasoning.translator import translate_to_english, translate_to_romanian
from config.eval_config import EVAL_CONFIG, EvalConfig
from config.prompts import LOW_CONFIDENCE_MESSAGE, build_context_block
from config.settings import BASE_SYSTEM_PROMPT, SETTINGS
from models import (
    EvaluatorResult,
    GuardrailResult,
    LLMRequest,
    LLMResponse,
    OrchestratorResponse,
    QueryRequest,
    RetrievalResult,
)
from rag.retrieval.embeddings import using_fallback_embeddings
from rag.retrieval.retriever import retrieve_top_similar

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OrchestratorDependencies:
    guardrail: Callable[[str], GuardrailResult] = apply_guardrails
    retrieve: Callable[[str, int, dict[str, str] | None], RetrievalResult] = retrieve_top_similar
    llm_call: Callable[[LLMRequest], LLMResponse] = llm_ask_request
    evaluator: Callable[[str, str, list[str] | None], EvaluatorResult] = evaluate_response
    translate_to_english: Callable[[str], str] = translate_to_english
    translate_to_romanian: Callable[[list[str]], list[str]] = translate_to_romanian


class Orchestrator:
    def __init__(
        self,
        deps: OrchestratorDependencies | None = None,
        eval_config: EvalConfig | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._deps = deps or OrchestratorDependencies()
        self._eval_config = eval_config or EVAL_CONFIG
        self._system_prompt = system_prompt or BASE_SYSTEM_PROMPT

    def run(self, request: QueryRequest) -> OrchestratorResponse:
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

        query_en = self._safe_translate_to_english(request.query)
        retrieval_filters = self._build_retrieval_filters(request.filters)
        retrieval_result = self._deps.retrieve(query_en, request.top_k, retrieval_filters)
        min_score = 0.0 if using_fallback_embeddings() else SETTINGS.retrieval_min_score
        if not retrieval_result.hits or retrieval_result.max_score() < min_score:
            return OrchestratorResponse(
                response=LOW_CONFIDENCE_MESSAGE,
                provider=None,
                model=None,
                retries=0,
                guardrail=guardrail_result,
                evaluator=None,
                retrieval=retrieval_result,
                context_lines=[],
            )
        context_lines = retrieval_result.context_lines(with_score=True)

        if request.language.lower().startswith("ro"):
            context_lines = self._safe_translate_to_romanian(context_lines)

        base_request = LLMRequest(
            system_prompt=self._system_prompt,
            user_message=request.query,
            context_block=build_context_block(context_lines),
        )

        max_attempts = max(self._eval_config.max_retries + 1, 1)
        last_eval: EvaluatorResult | None = None
        last_response: LLMResponse | None = None

        for attempt in range(max_attempts):
            provider = self._select_provider(attempt)
            attempt_request = self._apply_retry_guidance(base_request, last_eval)
            attempt_request.provider = provider
            last_response = self._deps.llm_call(attempt_request)
            last_eval = self._deps.evaluator(request.query, last_response.content, context_lines)
            self._log_evaluator_result(attempt, provider, last_eval)

            if last_eval.passed or not last_eval.retry_recommended:
                break

        retries = max((attempt + 1) - 1, 0)
        final_response = last_response.content if last_response else None
        if final_response is not None and retrieval_result is not None:
            final_response = append_retrieved_chunks_block(final_response, retrieval_result)
            if SETTINGS.retrieval_mode == "hybrid":
                citations = build_citation_rows(retrieval_result)
                final_response = append_citation_block(final_response, citations)

        return OrchestratorResponse(
            response=final_response,
            provider=last_response.provider if last_response else None,
            model=last_response.model if last_response else None,
            retries=retries,
            guardrail=guardrail_result,
            evaluator=last_eval,
            retrieval=retrieval_result,
            context_lines=context_lines,
        )

    @staticmethod
    def _build_retrieval_filters(
        filters: dict[str, str] | None,
    ) -> dict[str, str] | None:
        normalized = dict(filters or {})
        if SETTINGS.retrieval_mode != "hybrid":
            return normalized or None

        normalized["__graph_depth"] = str(SETTINGS.graph_traversal_depth)
        normalized["__vector_weight"] = str(SETTINGS.hybrid_vector_weight)
        normalized["__graph_weight"] = str(SETTINGS.hybrid_graph_weight)
        return normalized

    @staticmethod
    def _apply_retry_guidance(
        base_request: LLMRequest,
        last_eval: EvaluatorResult | None,
    ) -> LLMRequest:
        if not last_eval or last_eval.passed or not last_eval.reasons:
            return LLMRequest(
                system_prompt=base_request.system_prompt,
                user_message=base_request.user_message,
                context_block=base_request.context_block,
                temperature=base_request.temperature,
                provider=base_request.provider,
            )

        guidance = "Revise your answer to address: " + ", ".join(last_eval.reasons) + "."
        revised_message = f"{base_request.user_message}\n\n{guidance}"
        return LLMRequest(
            system_prompt=base_request.system_prompt,
            user_message=revised_message,
            context_block=base_request.context_block,
            temperature=base_request.temperature,
            provider=base_request.provider,
        )

    @staticmethod
    def _log_evaluator_result(attempt: int, provider: str, result: EvaluatorResult) -> None:
        logger.info(
            "Evaluator result",
            extra={
                "attempt": attempt,
                "provider": provider,
                "passed": result.passed,
                "score": result.score,
                "reasons": result.reasons,
                "retry_recommended": result.retry_recommended,
            },
        )

    def _safe_translate_to_english(self, text: str) -> str:
        try:
            return self._deps.translate_to_english(text)
        except Exception:
            return text

    def _safe_translate_to_romanian(self, items: list[str]) -> list[str]:
        if not items:
            return []
        try:
            return self._deps.translate_to_romanian(items)
        except Exception:
            return items

    def _select_provider(self, attempt: int) -> str:
        primary = SETTINGS.llm_provider
        fallback_order = [primary]
        for candidate in getattr(self._eval_config, "provider_fallback_order", []):
            if candidate not in fallback_order:
                fallback_order.append(candidate)

        if attempt < len(fallback_order):
            return fallback_order[attempt]
        return primary
