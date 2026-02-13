from __future__ import annotations

import unittest

from guardrails.rules import apply_guardrails as apply_guardrails_legacy
from models import (
    GuardrailResult,
    LLMRequest,
    LLMResponse,
    QueryRequest,
    RetrievalHit,
    RetrievalResult,
    evaluator_result_from_dict,
    llm_response_from_dict,
    serialize_to_json_compatible,
)


class TestModels(unittest.TestCase):
    def test_query_request_validation_rejects_empty_query(self) -> None:
        with self.assertRaises(ValueError):
            QueryRequest(query="  ")

    def test_query_request_from_dict_defaults(self) -> None:
        payload = {"query": "Care sunt simptomele gripei?"}
        request = QueryRequest.from_dict(payload)
        self.assertEqual(request.query, "Care sunt simptomele gripei?")
        self.assertEqual(request.top_k, 3)
        self.assertEqual(request.language, "ro")

    def test_guardrail_result_roundtrip(self) -> None:
        model = GuardrailResult(
            is_emergency=True,
            is_valid=False,
            message="Urgent",
            reason_code="KEYWORD_EMERGENCY",
            confidence=0.95,
        )
        roundtrip = GuardrailResult.from_dict(model.to_dict())
        self.assertEqual(roundtrip, model)

    def test_retrieval_result_context_and_titles(self) -> None:
        result = RetrievalResult(
            hits=[
                RetrievalHit(title="A", text="alpha", score=0.9),
                RetrievalHit(title="B", text="beta", score=0.5),
            ]
        )
        self.assertEqual(result.titles(), ["A", "B"])
        lines = result.context_lines(with_score=True)
        self.assertTrue(lines[0].startswith("alpha"))
        self.assertIn("(0.9000)", lines[0])

    def test_llm_request_builds_messages(self) -> None:
        request = LLMRequest(
            system_prompt="sys",
            user_message="question",
            context_block="- c1\n- c2",
        )
        messages = request.messages()
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("question", messages[1]["content"])
        self.assertIn("- c1", messages[1]["content"])

    def test_serde_helpers_for_llm_and_evaluator_results(self) -> None:
        llm_response = llm_response_from_dict({"content": "ok", "provider": "openai", "model": "m1"})
        self.assertEqual(llm_response, LLMResponse(content="ok", provider="openai", model="m1"))

        eval_result = evaluator_result_from_dict(
            {"passed": True, "score": 0.9, "reasons": ["a"], "retry_recommended": False}
        )
        payload = serialize_to_json_compatible(eval_result)
        self.assertEqual(payload["passed"], True)
        self.assertEqual(payload["score"], 0.9)
        self.assertEqual(payload["reasons"], ["a"])

    def test_legacy_guardrail_shim_returns_dict(self) -> None:
        result = apply_guardrails_legacy("nu pot respira")
        self.assertIsInstance(result, dict)
        self.assertTrue(result["is_emergency"])
        self.assertFalse(result["is_valid"])
        self.assertIn("message", result)


if __name__ == "__main__":
    unittest.main()

