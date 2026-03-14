from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent.evaluation.benchmark import load_retrieval_benchmark_queries
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

    def test_load_retrieval_benchmark_queries_reads_intrebare_entries(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            suffix=".json",
            encoding="utf-8",
        ) as handle:
            json.dump(
                [
                    {"id": 1, "intrebare": "Prima intrebare"},
                    {"id": 2, "intrebare": "A doua intrebare"},
                ],
                handle,
                ensure_ascii=False,
            )
            temp_json = handle.name
        try:
            probes = load_retrieval_benchmark_queries(temp_json)
            self.assertEqual(probes, ["Prima intrebare", "A doua intrebare"])
        finally:
            Path(temp_json).unlink(missing_ok=True)

    def test_load_retrieval_benchmark_queries_raises_on_missing_file(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_retrieval_benchmark_queries("data/dataset/does-not-exist.json")


if __name__ == "__main__":
    unittest.main()
