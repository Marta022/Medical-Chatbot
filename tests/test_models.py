from __future__ import annotations

import unittest

from agent.guardrail.rules_engine import apply_guardrails
from models import (
    GuardrailResult,
    LLMRequest,
    LLMResponse,
    MedicalEntity,
    MedicalRelation,
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
        self.assertIsNone(request.filters)

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
            ],
            provenance="vector",
        )
        self.assertEqual(result.titles(), ["A", "B"])
        lines = result.context_lines(with_score=True)
        self.assertTrue(lines[0].startswith("alpha"))
        self.assertIn("(0.9000)", lines[0])
        self.assertEqual(result.to_dict()["provenance"], "vector")

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
        llm_response = llm_response_from_dict(
            {"content": "ok", "provider": "openai", "model": "m1"}
        )
        self.assertEqual(llm_response, LLMResponse(content="ok", provider="openai", model="m1"))

        eval_result = evaluator_result_from_dict(
            {"passed": True, "score": 0.9, "reasons": ["a"], "retry_recommended": False}
        )
        payload = serialize_to_json_compatible(eval_result)
        self.assertEqual(payload["passed"], True)
        self.assertEqual(payload["score"], 0.9)
        self.assertEqual(payload["reasons"], ["a"])

    def test_apply_guardrails_returns_guardrail_result(self) -> None:
        result = apply_guardrails("nu pot respira")
        self.assertIsInstance(result, GuardrailResult)
        self.assertTrue(result.is_emergency)
        self.assertFalse(result.is_valid)
        self.assertTrue(bool(result.message))

    def test_medical_entity_to_dict(self) -> None:
        entity = MedicalEntity(
            entity_type="disease",
            mention_text="mi",
            canonical_form="myocardial infarction",
            confidence=0.85,
            source_file="doc.pdf",
            page=2,
            chunk_id="abc",
        )
        payload = entity.to_dict()
        self.assertEqual(payload["entity_type"], "disease")
        self.assertEqual(payload["canonical_form"], "myocardial infarction")
        self.assertEqual(payload["source_file"], "doc.pdf")

    def test_medical_relation_to_dict(self) -> None:
        relation = MedicalRelation(
            predicate="drug_treats_disease",
            source_entity_id="drug-id",
            source_entity_type="drug",
            source_canonical_form="aspirina",
            target_entity_id="disease-id",
            target_entity_type="disease",
            target_canonical_form="myocardial infarction",
            confidence=0.84,
            source_file="doc.pdf",
            page=4,
            chunk_id="chunk-4",
        )
        payload = relation.to_dict()
        self.assertEqual(payload["predicate"], "drug_treats_disease")
        self.assertEqual(payload["source_entity_type"], "drug")
        self.assertEqual(payload["target_entity_type"], "disease")


if __name__ == "__main__":
    unittest.main()
