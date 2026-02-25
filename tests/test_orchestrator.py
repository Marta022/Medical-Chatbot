from __future__ import annotations

import unittest

from agent.orchestrator.orchestrator import Orchestrator, OrchestratorDependencies
from config.eval_config import EvalConfig
from config.settings import SETTINGS
from models import (
    EvaluatorResult,
    GuardrailResult,
    LLMRequest,
    LLMResponse,
    QueryRequest,
    RetrievalHit,
    RetrievalResult,
)


class TestOrchestrator(unittest.TestCase):
    def test_guardrail_blocks_short_circuit(self) -> None:
        def guardrail(_query: str) -> GuardrailResult:
            return GuardrailResult(is_valid=False, message="blocked", reason_code="BLOCKED")

        deps = OrchestratorDependencies(
            guardrail=guardrail,
            retrieve=lambda _q, _k, _f: RetrievalResult(),
            llm_call=lambda _r: LLMResponse(content="nope", provider="openai"),
            evaluator=lambda _q, _r, _c: EvaluatorResult(passed=True, score=1.0),
            translate_to_english=lambda text: text,
            translate_to_romanian=lambda items: items,
        )

        orchestrator = Orchestrator(deps=deps)
        result = orchestrator.run(QueryRequest(query="test", top_k=1))

        self.assertEqual(result.response, "blocked")
        self.assertIsNone(result.evaluator)
        self.assertIsNone(result.retrieval)
        self.assertEqual(result.retries, 0)

    def test_happy_path_returns_response(self) -> None:
        def guardrail(_query: str) -> GuardrailResult:
            return GuardrailResult(is_valid=True)

        def retrieve(_query: str, _top_k: int, _filters: dict[str, str] | None) -> RetrievalResult:
            return RetrievalResult(
                hits=[RetrievalHit(title="t1", text="t1 body", score=0.9, source="unit")]
            )

        def llm_call(request: LLMRequest) -> LLMResponse:
            return LLMResponse(content="ok", provider=request.provider or "openai", model="unit")

        def evaluator(_q: str, _r: str, _c: list[str] | None) -> EvaluatorResult:
            return EvaluatorResult(passed=True, score=1.0, reasons=[])

        deps = OrchestratorDependencies(
            guardrail=guardrail,
            retrieve=retrieve,
            llm_call=llm_call,
            evaluator=evaluator,
            translate_to_english=lambda text: text,
            translate_to_romanian=lambda items: items,
        )

        orchestrator = Orchestrator(deps=deps)
        result = orchestrator.run(QueryRequest(query="test", top_k=1))

        self.assertEqual(result.response, "ok")
        self.assertTrue(result.guardrail.is_valid)
        self.assertEqual(result.retries, 0)
        self.assertIsNotNone(result.evaluator)
        self.assertEqual(result.provider, SETTINGS.llm_provider)

    def test_retry_uses_fallback_provider(self) -> None:
        providers_used: list[str] = []
        eval_calls = {"count": 0}

        def guardrail(_query: str) -> GuardrailResult:
            return GuardrailResult(is_valid=True)

        def retrieve(_query: str, _top_k: int, _filters: dict[str, str] | None) -> RetrievalResult:
            return RetrievalResult(
                hits=[RetrievalHit(title="t1", text="t1 body", score=0.9, source="unit")]
            )

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
                )
            return EvaluatorResult(passed=True, score=0.9, reasons=[])

        deps = OrchestratorDependencies(
            guardrail=guardrail,
            retrieve=retrieve,
            llm_call=llm_call,
            evaluator=evaluator,
            translate_to_english=lambda text: text,
            translate_to_romanian=lambda items: items,
        )

        eval_config = EvalConfig(max_retries=1, provider_fallback_order=("openai", "ollama"))
        orchestrator = Orchestrator(deps=deps, eval_config=eval_config)
        result = orchestrator.run(QueryRequest(query="test", top_k=1))

        self.assertEqual(result.retries, 1)
        self.assertEqual(len(providers_used), 2)
        self.assertEqual(providers_used[0], SETTINGS.llm_provider)
        self.assertNotEqual(providers_used[0], providers_used[1])

    def test_low_confidence_fallback_skips_llm(self) -> None:
        llm_called = {"count": 0}

        def guardrail(_query: str) -> GuardrailResult:
            return GuardrailResult(is_valid=True)

        def retrieve(_query: str, _top_k: int, _filters: dict[str, str] | None) -> RetrievalResult:
            return RetrievalResult(hits=[])

        def llm_call(_request: LLMRequest) -> LLMResponse:
            llm_called["count"] += 1
            return LLMResponse(content="ok", provider="openai")

        deps = OrchestratorDependencies(
            guardrail=guardrail,
            retrieve=retrieve,
            llm_call=llm_call,
            evaluator=lambda _q, _r, _c: EvaluatorResult(passed=True, score=1.0),
            translate_to_english=lambda text: text,
            translate_to_romanian=lambda items: items,
        )

        orchestrator = Orchestrator(deps=deps)
        result = orchestrator.run(QueryRequest(query="test", top_k=1))

        self.assertEqual(llm_called["count"], 0)
        self.assertIsNone(result.evaluator)

    def test_retry_appends_guidance_to_user_message(self) -> None:
        messages: list[str] = []
        eval_calls = {"count": 0}

        def guardrail(_query: str) -> GuardrailResult:
            return GuardrailResult(is_valid=True)

        def retrieve(_query: str, _top_k: int, _filters: dict[str, str] | None) -> RetrievalResult:
            return RetrievalResult(
                hits=[RetrievalHit(title="t1", text="t1 body", score=0.9, source="unit")]
            )

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

        deps = OrchestratorDependencies(
            guardrail=guardrail,
            retrieve=retrieve,
            llm_call=llm_call,
            evaluator=evaluator,
            translate_to_english=lambda text: text,
            translate_to_romanian=lambda items: items,
        )

        eval_config = EvalConfig(max_retries=1, provider_fallback_order=("openai", "ollama"))
        orchestrator = Orchestrator(deps=deps, eval_config=eval_config)
        orchestrator.run(QueryRequest(query="test", top_k=1))

        self.assertEqual(len(messages), 2)
        self.assertIn("Revise your answer to address: needs_more_context.", messages[1])


if __name__ == "__main__":
    unittest.main()
