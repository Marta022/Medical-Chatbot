from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent.evaluation.benchmark import (
    _extract_option_letters,
    load_retrieval_answer_key,
    run_retrieval_benchmark,
)


class TestBenchmark(unittest.TestCase):
    def test_extract_option_letters_uses_answer_segment_only(self) -> None:
        raw_response = (
            "RASPUNS: C,D\n\n"
            "Most similar chunks:\n"
            "A) fragment din context\n"
            "B) alt fragment"
        )
        self.assertEqual(_extract_option_letters(raw_response), {"C", "D"})

    def test_load_retrieval_answer_key_supports_multiple_answers(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as handle:
            handle.write("521: A,C\n522: B\n")
            key_path = handle.name
        try:
            answer_key = load_retrieval_answer_key(key_path)
            self.assertEqual(answer_key[521], {"A", "C"})
            self.assertEqual(answer_key[522], {"B"})
        finally:
            Path(key_path).unlink(missing_ok=True)

    def test_run_retrieval_benchmark_computes_set_metrics(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as bench_handle:
            json.dump(
                [
                    {
                        "id": 521,
                        "intrebare": "Q1",
                        "A": "a",
                        "B": "b",
                        "C": "c",
                        "D": "d",
                        "E": "e",
                    }
                ],
                bench_handle,
                ensure_ascii=False,
            )
            benchmark_path = bench_handle.name

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as key_handle:
            key_handle.write("521: A,C\n")
            key_path = key_handle.name

        try:
            result = run_retrieval_benchmark(
                benchmark_json_path=benchmark_path,
                answer_key_path=key_path,
                ask_fn=lambda _prompt: "RASPUNS: A, C",
            )
            self.assertEqual(result["evaluated_count"], 1)
            self.assertEqual(result["aggregate"]["exact_match_rate"], 1.0)
            self.assertEqual(result["aggregate"]["macro_f1"], 1.0)
            self.assertEqual(result["rows"][0]["predicted_answers"], ["A", "C"])
        finally:
            Path(benchmark_path).unlink(missing_ok=True)
            Path(key_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
