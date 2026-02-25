from __future__ import annotations

import unittest

from agent.evaluation.evaluator import evaluate_response
from config.eval_config import EVAL_CONFIG


class TestEvaluator(unittest.TestCase):
    def test_empty_response_fails(self) -> None:
        result = evaluate_response("intrebare", "")
        self.assertFalse(result.passed)
        self.assertEqual(result.score, 0.0)
        self.assertIn("empty_response", result.reasons)
        self.assertTrue(result.retry_recommended)

    def test_short_response_penalized_but_passes(self) -> None:
        result = evaluate_response("intrebare", "scurt ok")
        self.assertIn("response_too_short", result.reasons)
        self.assertGreaterEqual(result.score, EVAL_CONFIG.pass_score)
        self.assertTrue(result.passed)
        self.assertFalse(result.retry_recommended)

    def test_context_unknown_penalty(self) -> None:
        response = "I don't know based on the available data."
        result = evaluate_response("intrebare", response, context_lines=["ctx"])
        self.assertIn("context_available_but_unknown_answer", result.reasons)
        self.assertGreaterEqual(result.score, EVAL_CONFIG.pass_score)
        self.assertTrue(result.passed)
        self.assertFalse(result.retry_recommended)


if __name__ == "__main__":
    unittest.main()
