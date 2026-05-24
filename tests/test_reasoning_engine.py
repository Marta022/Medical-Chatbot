from __future__ import annotations

import unittest
from unittest.mock import patch

from agent.reasoning.engine import ReasoningDependencies, ReasoningEngine, ReasoningInput
from config.eval_config import EvalConfig
from config.prompts import REJECTED_RESPONSE_MESSAGE
from config.settings import SETTINGS, AppSettings
from models import EvaluatorResult, LLMRequest, LLMResponse, RetrievalHit, RetrievalResult


class TestReasoningEngine(unittest.TestCase):
    def test_low_confidence_fallback_skips_llm(self) -> None:
        llm_called = {"count": 0}

        def llm_call(_request: LLMRequest) -> LLMResponse:
            llm_called["count"] += 1
            return LLMResponse(content="ok", provider="openai")

        deps = ReasoningDependencies(
            retrieve=lambda _q, _k, _f: RetrievalResult(hits=[]),
            llm_call=llm_call,
            evaluator=lambda _q, _r, _c: EvaluatorResult(passed=True, score=1.0),
        )

        result = ReasoningEngine(deps=deps).run(ReasoningInput(query="test", top_k=1))

        self.assertEqual(llm_called["count"], 0)
        self.assertIsNone(result.evaluator)
        self.assertIsNotNone(result.retrieval)

    def test_retry_uses_fallback_provider(self) -> None:
        providers_used: list[str] = []
        eval_calls = {"count": 0}

        def llm_call(request: LLMRequest) -> LLMResponse:
            provider = request.provider or SETTINGS.llm_provider
            providers_used.append(provider)
            return LLMResponse(content=f"ok-{provider}", provider=provider, model="unit")

        def evaluator(_q: str, _r: str, _c: list[str] | None) -> EvaluatorResult:
            eval_calls["count"] += 1
            if eval_calls["count"] == 1:
                return EvaluatorResult(
                    passed=False,
                    score=0.4,
                    reasons=["too_short"],
                    retry_recommended=True,
                    retry_strategy="switch_llm",
                )
            return EvaluatorResult(passed=True, score=0.9, reasons=[])

        deps = ReasoningDependencies(
            retrieve=lambda _q, _k, _f: RetrievalResult(
                hits=[RetrievalHit(title="t1", text="t1 body", score=0.9, source="unit")]
            ),
            llm_call=llm_call,
            evaluator=evaluator,
        )
        eval_config = EvalConfig(max_retries=1, provider_fallback_order=("openai", "ollama"))

        result = ReasoningEngine(deps=deps, eval_config=eval_config).run(
            ReasoningInput(query="test", top_k=1)
        )

        self.assertEqual(result.retries, 1)
        self.assertEqual(len(providers_used), 2)
        self.assertEqual(providers_used[0], SETTINGS.llm_provider)
        self.assertNotEqual(providers_used[0], providers_used[1])

    def test_retry_appends_guidance_to_user_message(self) -> None:
        messages: list[str] = []
        eval_calls = {"count": 0}

        def llm_call(request: LLMRequest) -> LLMResponse:
            messages.append(request.user_message)
            return LLMResponse(content="ok", provider=request.provider or "openai", model="unit")

        def evaluator(_q: str, _r: str, _c: list[str] | None) -> EvaluatorResult:
            eval_calls["count"] += 1
            if eval_calls["count"] == 1:
                return EvaluatorResult(
                    passed=False,
                    score=0.4,
                    reasons=["needs_more_context"],
                    retry_recommended=True,
                )
            return EvaluatorResult(passed=True, score=0.9, reasons=[])

        deps = ReasoningDependencies(
            retrieve=lambda _q, _k, _f: RetrievalResult(
                hits=[RetrievalHit(title="t1", text="t1 body", score=0.9, source="unit")]
            ),
            llm_call=llm_call,
            evaluator=evaluator,
        )
        eval_config = EvalConfig(max_retries=1, provider_fallback_order=("openai", "ollama"))

        ReasoningEngine(deps=deps, eval_config=eval_config).run(
            ReasoningInput(query="test", top_k=1)
        )

        self.assertEqual(len(messages), 2)
        self.assertIn("Revise your answer to address: needs_more_context.", messages[1])

    def test_rejected_response_after_retry_budget_is_replaced_with_safe_message(self) -> None:
        deps = ReasoningDependencies(
            retrieve=lambda _q, _k, _f: RetrievalResult(
                hits=[RetrievalHit(title="t1", text="t1 body", score=0.9, source="unit")]
            ),
            llm_call=lambda request: LLMResponse(
                content="unsafe final draft",
                provider=request.provider or "openai",
                model="unit",
            ),
            evaluator=lambda _q, _r, _c: EvaluatorResult(
                passed=False,
                score=0.0,
                reasons=["unsafe_advice"],
                retry_recommended=True,
                retry_strategy="switch_llm",
            ),
        )
        eval_config = EvalConfig(max_retries=1, provider_fallback_order=("openai", "ollama"))

        result = ReasoningEngine(deps=deps, eval_config=eval_config).run(
            ReasoningInput(query="test", top_k=1)
        )

        self.assertEqual(result.response, REJECTED_RESPONSE_MESSAGE)
        self.assertEqual(result.retries, 1)
        self.assertFalse(result.evaluator.passed)
        self.assertNotIn("Most similar chunks:", result.response)

    def test_refusal_with_context_stops_after_first_attempt_and_uses_safe_message(self) -> None:
        calls = {"llm": 0}

        def llm_call(request: LLMRequest) -> LLMResponse:
            calls["llm"] += 1
            return LLMResponse(
                content="I don't know based on the available data.",
                provider=request.provider or "openai",
                model="unit",
            )

        deps = ReasoningDependencies(
            retrieve=lambda _q, _k, _f: RetrievalResult(
                hits=[RetrievalHit(title="t1", text="t1 body", score=0.9, source="unit")]
            ),
            llm_call=llm_call,
            evaluator=lambda _q, _r, _c: EvaluatorResult(
                passed=False,
                score=0.3,
                reasons=["refused_with_context"],
                retry_recommended=False,
            ),
        )

        result = ReasoningEngine(deps=deps, eval_config=EvalConfig(max_retries=3)).run(
            ReasoningInput(query="test", top_k=1)
        )

        self.assertEqual(calls["llm"], 1)
        self.assertEqual(result.retries, 0)
        self.assertEqual(result.response, REJECTED_RESPONSE_MESSAGE)

    def test_hybrid_mode_injects_filters_and_citations(self) -> None:
        captured_filters: list[dict[str, str] | None] = []

        def retrieve(_query: str, _top_k: int, filters: dict[str, str] | None) -> RetrievalResult:
            captured_filters.append(filters)
            return RetrievalResult(
                hits=[
                    RetrievalHit(
                        title="Doc",
                        text="Context",
                        score=0.9,
                        source="pdf",
                        source_file="doc.pdf",
                        page=2,
                        section="1.2",
                        chunk_id="chunk-2",
                    )
                ]
            )

        deps = ReasoningDependencies(
            retrieve=retrieve,
            llm_call=lambda request: LLMResponse(
                content="ok",
                provider=request.provider or SETTINGS.llm_provider,
                model="unit",
            ),
            evaluator=lambda _q, _r, _c: EvaluatorResult(passed=True, score=1.0, reasons=[]),
        )
        hybrid_settings = AppSettings(
            retrieval_mode="hybrid",
            graph_traversal_depth=2,
            hybrid_vector_weight=1.0,
            hybrid_graph_weight=0.7,
        )

        with patch("agent.reasoning.engine.SETTINGS", hybrid_settings):
            result = ReasoningEngine(deps=deps).run(ReasoningInput(query="test", top_k=1))

        self.assertEqual(len(captured_filters), 1)
        self.assertIsNotNone(captured_filters[0])
        self.assertEqual(captured_filters[0]["__graph_depth"], "2")
        self.assertEqual(captured_filters[0]["__vector_weight"], "1.0")
        self.assertEqual(captured_filters[0]["__graph_weight"], "0.7")
        self.assertIsNotNone(result.response)
        self.assertIn("Citations:", result.response)
        self.assertIn("source_file=doc.pdf", result.response)


if __name__ == "__main__":
    unittest.main()
