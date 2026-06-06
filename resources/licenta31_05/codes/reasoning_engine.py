"""Reasoning engine that decides retrieval, prompting, and retry strategy."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from agent.evaluation.evaluator import evaluate_response
from agent.orchestrator.citations import (
    append_citation_block,
    append_retrieved_chunks_block,
    build_citation_rows,
)
from config.eval_config import EVAL_CONFIG, EvalConfig
from config.prompts import LOW_CONFIDENCE_MESSAGE, REJECTED_RESPONSE_MESSAGE, build_context_block
from config.settings import BASE_SYSTEM_PROMPT, SETTINGS
from llm.llm_router import llm_ask_request
from models import EvaluatorResult, LLMRequest, LLMResponse, RetrievalResult
from rag.retrieval.retriever import retrieve_top_similar

logger = logging.getLogger(__name__)
RETRY_GUIDANCE_PREFIX = "Revise your answer to address: "
ADAPTIVE_RETRY_HEADER = "Retry instruction from evaluator:"


@dataclass(frozen=True)
class ReasoningInput:
    """Input payload required for one reasoning pass."""

    query: str
    top_k: int
    language: str = "ro"
    filters: dict[str, str] | None = None


@dataclass(frozen=True)
class ReasoningDependencies:
    """Injected dependencies used by the reasoning engine."""

    retrieve: Callable[[str, int, dict[str, str] | None], RetrievalResult] = retrieve_top_similar
    llm_call: Callable[[LLMRequest], LLMResponse] = llm_ask_request
    evaluator: Callable[[str, str, list[str] | None], EvaluatorResult] = evaluate_response


@dataclass(frozen=True)
class ReasoningOutput:
    """Result envelope produced by the reasoning engine."""

    response: str | None
    provider: str | None
    model: str | None
    retries: int
    evaluator: EvaluatorResult | None
    retrieval: RetrievalResult | None
    context_lines: list[str]


class ReasoningEngine:
    """Decide how to generate the final answer (RAG, prompting, retries, provider fallback)."""

    def __init__(
        self,
        deps: ReasoningDependencies | None = None,
        eval_config: EvalConfig | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._deps = deps or ReasoningDependencies()
        self._eval_config = eval_config or EVAL_CONFIG
        self._system_prompt = system_prompt or BASE_SYSTEM_PROMPT

    def run(self, request: ReasoningInput) -> ReasoningOutput:
        """Execute retrieval, generation, and evaluation until pass or retry budget is exhausted."""

        retrieval_filters = self._build_retrieval_filters(request.filters)
        retrieval_result = self._deps.retrieve(request.query, request.top_k, retrieval_filters)
        logger.info(
            "Retrieval result",
            extra={
                "provenance": retrieval_result.provenance,
                "hit_count": len(retrieval_result.hits),
                "max_score": retrieval_result.max_score() if retrieval_result.hits else 0.0,
            },
        )
        min_score = SETTINGS.retrieval_min_score
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

        max_attempts = max(self._eval_config.max_retries + 1, 1)
        last_eval: EvaluatorResult | None = None
        last_response: LLMResponse | None = None
        attempt = 0

        for attempt in range(max_attempts):
            provider = self._select_provider(attempt, last_eval)
            attempt_request = self._apply_retry_guidance(base_request, last_eval)
            attempt_request.provider = provider
            last_response = self._deps.llm_call(attempt_request)
            last_eval = self._deps.evaluator(request.query, last_response.content, context_lines)
            self._log_evaluator_result(attempt, provider, last_eval)

            if last_eval.passed or not last_eval.retry_recommended:
                break

        retries = max((attempt + 1) - 1, 0)
        is_accepted = last_eval is not None and last_eval.passed
        final_response = last_response.content if last_response else None
        if final_response is not None and not is_accepted:
            final_response = REJECTED_RESPONSE_MESSAGE
        elif final_response is not None:
            final_response = append_retrieved_chunks_block(final_response, retrieval_result)
            if SETTINGS.retrieval_mode == "hybrid":
                citations = build_citation_rows(retrieval_result)
                final_response = append_citation_block(final_response, citations)

        return ReasoningOutput(
            response=final_response,
            provider=last_response.provider if last_response else None,
            model=last_response.model if last_response else None,
            retries=retries,
            evaluator=last_eval,
            retrieval=retrieval_result,
            context_lines=context_lines,
        )

    @staticmethod
    def _build_retrieval_filters(filters: dict[str, str] | None) -> dict[str, str] | None:
        """Attach graph retrieval controls when hybrid retrieval is enabled."""

        normalized = dict(filters or {})
        if SETTINGS.retrieval_mode != "hybrid":
            return normalized or None

        normalized["__graph_depth"] = str(SETTINGS.graph_traversal_depth)
        normalized["__vector_weight"] = str(SETTINGS.hybrid_vector_weight)
        normalized["__graph_weight"] = str(SETTINGS.hybrid_graph_weight)
        return normalized

    @staticmethod
    def _clone_llm_request(
        base_request: LLMRequest,
        *,
        user_message: str | None = None,
    ) -> LLMRequest:
        """Create a copy of an LLM request with optional user message override."""

        return LLMRequest(
            system_prompt=base_request.system_prompt,
            user_message=user_message if user_message is not None else base_request.user_message,
            context_block=base_request.context_block,
            temperature=base_request.temperature,
            provider=base_request.provider,
        )

    @classmethod
    def _apply_retry_guidance(
        cls,
        base_request: LLMRequest,
        last_eval: EvaluatorResult | None,
    ) -> LLMRequest:
        """Copy base request and append evaluator guidance for retry attempts."""

        if not last_eval or last_eval.passed:
            return cls._clone_llm_request(base_request)
        if not last_eval.adaptive_prompt and not last_eval.reasons:
            return cls._clone_llm_request(base_request)

        if last_eval.adaptive_prompt:
            guidance = f"{ADAPTIVE_RETRY_HEADER}\n{last_eval.adaptive_prompt}"
        else:
            guidance = RETRY_GUIDANCE_PREFIX + ", ".join(last_eval.reasons) + "."
        revised_message = f"{base_request.user_message}\n\n{guidance}"
        return cls._clone_llm_request(base_request, user_message=revised_message)

    @staticmethod
    def _log_evaluator_result(attempt: int, provider: str, result: EvaluatorResult) -> None:
        """Log evaluator output for each generation attempt."""

        logger.info(
            "Evaluator result",
            extra={
                "attempt": attempt,
                "provider": provider,
                "passed": result.passed,
                "score": result.score,
                "reasons": result.reasons,
                "retry_recommended": result.retry_recommended,
                "failure_types": result.failure_types,
                "retry_strategy": result.retry_strategy,
                "judge_used": result.judge_used,
            },
        )

    def _select_provider(self, attempt: int, last_eval: EvaluatorResult | None) -> str:
        """Pick provider for the current attempt using configured fallback order."""

        primary = SETTINGS.llm_provider
        if attempt == 0 or not last_eval or last_eval.retry_strategy != "switch_llm":
            return primary

        fallback_order = [primary]
        for candidate in getattr(self._eval_config, "provider_fallback_order", []):
            if candidate not in fallback_order:
                fallback_order.append(candidate)

        if attempt < len(fallback_order):
            return fallback_order[attempt]
        return primary
