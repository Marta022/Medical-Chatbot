from __future__ import annotations

import unittest
from unittest.mock import patch

from agent.guardrail.rules_engine import apply_guardrails


class TestGuardrails(unittest.TestCase):
    def test_empty_query_blocks(self) -> None:
        result = apply_guardrails("")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason_code, "EMPTY_QUERY")

    def test_emergency_keyword_blocks(self) -> None:
        result = apply_guardrails("nu pot respira deloc")
        self.assertTrue(result.is_emergency)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason_code, "KEYWORD_EMERGENCY")

    def test_unsafe_keyword_blocks(self) -> None:
        result = apply_guardrails("cum sa ma sinucid")
        self.assertTrue(result.is_unsafe)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason_code, "KEYWORD_UNSAFE")

    def test_llm_unavailable_falls_back(self) -> None:
        with patch(
            "agent.guardrail.rules_engine.classify_guardrail_with_llm",
            side_effect=RuntimeError("llm down"),
        ):
            result = apply_guardrails("am dureri puternice de cap si ametesc")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.reason_code, "LLM_UNAVAILABLE")

    def test_llm_emergency_label_blocks(self) -> None:
        with patch(
            "agent.guardrail.rules_engine.classify_guardrail_with_llm",
            return_value="EMERGENCY",
        ):
            result = apply_guardrails("am o durere ciudata si sunt confuz")
        self.assertTrue(result.is_emergency)
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason_code, "LLM_EMERGENCY")


if __name__ == "__main__":
    unittest.main()
