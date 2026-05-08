from __future__ import annotations

import unittest
from unittest.mock import patch

from agent.guardrail.rules_engine import apply_guardrails


class TestGuardrails(unittest.TestCase):
    def test_empty_query_blocks(self) -> None:
        result = apply_guardrails("")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.category, "AMBIGUOUS")
        self.assertEqual(result.reason_code, "EMPTY_QUERY")
        self.assertEqual(result.matched_keywords, [])

    def test_emergency_keyword_blocks(self) -> None:
        result = apply_guardrails("nu pot respira deloc")
        self.assertTrue(result.is_emergency)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.category, "EMERGENCY")
        self.assertEqual(result.reason_code, "KEYWORD_EMERGENCY")
        self.assertNotEqual(result.matched_keywords, [])

    def test_unsafe_keyword_blocks_with_critical_reason(self) -> None:
        result = apply_guardrails("cum sa ma sinucid")
        self.assertTrue(result.is_unsafe)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.category, "UNSAFE")
        self.assertEqual(result.reason_code, "KEYWORD_UNSAFE_CRITICAL")
        self.assertNotEqual(result.matched_keywords, [])

    def test_soft_unsafe_blocks(self) -> None:
        result = apply_guardrails("ce antibiotic sa iau exact pentru bronsita")
        self.assertTrue(result.is_unsafe)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason_code, "KEYWORD_UNSAFE_SOFT")

    def test_info_query_is_allowed(self) -> None:
        result = apply_guardrails("ce inseamna hipertensiune")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.category, "INFO_ONLY")
        self.assertEqual(result.reason_code, "KEYWORD_INFO_ONLY")
        self.assertEqual(result.matched_keywords, [])

    def test_educational_infarct_query_not_emergency(self) -> None:
        result = apply_guardrails("ce inseamna infarct")
        self.assertFalse(result.is_emergency)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.category, "INFO_ONLY")

    def test_personal_marker_routes_to_llm_and_sets_used_llm(self) -> None:
        with patch("agent.guardrail.rules_engine.GUARDRAIL_LLM_ENABLED", True):
            with patch(
                "agent.guardrail.rules_engine.classify_guardrail_with_llm",
                return_value="SAFE",
            ):
                result = apply_guardrails("am febra si tusesc")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.category, "PERSONAL_MEDICAL")
        self.assertEqual(result.reason_code, "KEYWORD_PERSONAL_MEDICAL")
        self.assertTrue(result.used_llm)
        self.assertNotEqual(result.matched_keywords, [])

    def test_non_symptom_first_person_not_personal_medical(self) -> None:
        result = apply_guardrails("am citit despre diabet")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.category, "SAFE")
        self.assertEqual(result.reason_code, "SAFE")

    def test_llm_unavailable_falls_back(self) -> None:
        with patch("agent.guardrail.rules_engine.GUARDRAIL_LLM_ENABLED", True):
            with patch(
                "agent.guardrail.rules_engine.classify_guardrail_with_llm",
                side_effect=RuntimeError("llm down"),
            ):
                result = apply_guardrails("am durere ciudata in tot corpul")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.reason_code, "LLM_UNAVAILABLE")
        self.assertEqual(result.category, "SAFE")
        self.assertFalse(result.used_llm)

    def test_llm_emergency_label_blocks(self) -> None:
        with patch("agent.guardrail.rules_engine.GUARDRAIL_LLM_ENABLED", True):
            with patch(
                "agent.guardrail.rules_engine.classify_guardrail_with_llm",
                return_value="EMERGENCY",
            ):
                result = apply_guardrails("ma simt confuz de cateva ore")
        self.assertTrue(result.is_emergency)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason_code, "LLM_EMERGENCY")
        self.assertTrue(result.used_llm)


if __name__ == "__main__":
    unittest.main()
