from __future__ import annotations

import unittest
from unittest.mock import patch

from agent.guardrail.llm_classifier import classify_guardrail_with_llm


class TestLLMClassifier(unittest.TestCase):
    def test_classifier_maps_labels(self) -> None:
        with patch("agent.guardrail.llm_classifier.llm_classify", return_value="EMERGENCY"):
            self.assertEqual(classify_guardrail_with_llm("q"), "EMERGENCY")

        with patch("agent.guardrail.llm_classifier.llm_classify", return_value="unsafe"):
            self.assertEqual(classify_guardrail_with_llm("q"), "UNSAFE")

        with patch("agent.guardrail.llm_classifier.llm_classify", return_value="SAFE"):
            self.assertEqual(classify_guardrail_with_llm("q"), "SAFE")

    def test_classifier_handles_unknown_label(self) -> None:
        with patch("agent.guardrail.llm_classifier.llm_classify", return_value="maybe"):
            self.assertEqual(classify_guardrail_with_llm("q"), "SAFE")

        with patch(
            "agent.guardrail.llm_classifier.llm_classify", return_value="EMERGENCY - urgent"
        ):
            self.assertEqual(classify_guardrail_with_llm("q"), "EMERGENCY")


if __name__ == "__main__":
    unittest.main()
