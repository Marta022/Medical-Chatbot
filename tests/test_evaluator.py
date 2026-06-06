from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent.benchmarking.benchmark import load_retrieval_benchmark_queries
from agent.evaluation.evaluator import evaluate_response
from agent.evaluation.failure_taxonomy import FailureType
from config.eval_config import EVAL_CONFIG


class TestEvaluator(unittest.TestCase):
    def test_evaluation_smoke_sample_passes(self) -> None:
        result = evaluate_response(
            query="Care sunt simptomele gripei?",
            response="Gripa include febra, frisoane, tuse si dureri musculare.",
            context_lines=["Simptome frecvente: febra, tuse, dureri musculare."],
        )
        self.assertTrue(result.passed)
        self.assertGreaterEqual(result.score, EVAL_CONFIG.pass_score)

    def test_empty_response_fails(self) -> None:
        result = evaluate_response("intrebare", "")
        self.assertFalse(result.passed)
        self.assertEqual(result.score, 0.0)
        self.assertIn(FailureType.EMPTY.value, result.reasons)
        self.assertIn(FailureType.EMPTY, result.failure_types)
        self.assertTrue(result.retry_recommended)
        self.assertIsNotNone(result.adaptive_prompt)

    def test_short_response_fails_with_adaptive_prompt(self) -> None:
        result = evaluate_response("intrebare", "scurt ok")
        self.assertIn(FailureType.TOO_SHORT.value, result.reasons)
        self.assertIn(FailureType.TOO_SHORT, result.failure_types)
        self.assertLess(result.score, EVAL_CONFIG.pass_score)
        self.assertFalse(result.passed)
        self.assertTrue(result.retry_recommended)
        self.assertEqual(result.retry_strategy, "adjust_prompt")
        self.assertIsNotNone(result.adaptive_prompt)

    def test_context_unknown_penalty(self) -> None:
        response = "I don't know based on the available data."
        result = evaluate_response("intrebare", response, context_lines=["ctx"])
        self.assertIn(FailureType.REFUSED_WITH_CONTEXT.value, result.reasons)
        self.assertIn(FailureType.REFUSED_WITH_CONTEXT, result.failure_types)
        self.assertFalse(result.passed)
        self.assertFalse(result.retry_recommended)

    def test_unsafe_advice_uses_switch_llm_strategy(self) -> None:
        result = evaluate_response(
            "Cat ibuprofen iau?",
            "Ia 400 mg la 8 ore.",
            context_lines=[],
        )
        self.assertIn(FailureType.UNSAFE_ADVICE, result.failure_types)
        self.assertEqual(result.retry_strategy, "switch_llm")

    def test_hallucination_risk_uses_switch_llm_strategy(self) -> None:
        result = evaluate_response(
            query="Care sunt simptomele gripei?",
            response=(
                "Gripa se vindeca instant in 24 de ore in toate cazurile si este intotdeauna "
                "usoara, fara exceptii."
            ),
            context_lines=["Simptome frecvente: febra, tuse, dureri musculare."],
        )
        self.assertIn(FailureType.HALLUCINATION_RISK, result.failure_types)
        self.assertEqual(result.retry_strategy, "switch_llm")

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
