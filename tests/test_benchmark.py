from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent.evaluation.benchmark import (
    _extract_option_letters,
    _requires_single_answer,
    load_retrieval_answer_key,
    load_retrieval_benchmark_items,
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
            self.assertFalse(result["guardrail_enabled_during_benchmark"])
            self.assertEqual(result["aggregate"]["exact_match_rate"], 1.0)
            self.assertEqual(result["aggregate"]["macro_f1"], 1.0)
            self.assertEqual(result["rows"][0]["predicted_answers"], ["A", "C"])
        finally:
            Path(benchmark_path).unlink(missing_ok=True)
            Path(key_path).unlink(missing_ok=True)

    def test_load_retrieval_benchmark_items_supports_alternative_json_shape(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as handle:
            json.dump(
                [
                    {
                        "question_id": 700,
                        "question": "Q alt",
                        "options": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
                    }
                ],
                handle,
                ensure_ascii=False,
            )
            benchmark_path = handle.name
        try:
            items = load_retrieval_benchmark_items(benchmark_path)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["id"], 700)
            self.assertEqual(items[0]["intrebare"], "Q alt")
            self.assertEqual(items[0]["choices"]["C"], "c")
        finally:
            Path(benchmark_path).unlink(missing_ok=True)

    def test_load_retrieval_answer_key_supports_json_raspuns_field(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as handle:
            json.dump(
                [
                    {"id": 102, "raspuns": "A"},
                    {"question_id": 103, "answers": ["B", "D"]},
                ],
                handle,
                ensure_ascii=False,
            )
            key_path = handle.name
        try:
            answer_key = load_retrieval_answer_key(key_path)
            self.assertEqual(answer_key[102], {"A"})
            self.assertEqual(answer_key[103], {"B", "D"})
        finally:
            Path(key_path).unlink(missing_ok=True)

    def test_run_retrieval_benchmark_reports_global_score_on_full_dataset(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as bench_handle:
            json.dump(
                [
                    {
                        "id": 1,
                        "intrebare": "Q1",
                        "A": "a",
                        "B": "b",
                        "C": "c",
                        "D": "d",
                        "E": "e",
                    },
                    {
                        "id": 2,
                        "intrebare": "Q2",
                        "A": "a",
                        "B": "b",
                        "C": "c",
                        "D": "d",
                        "E": "e",
                    },
                ],
                bench_handle,
                ensure_ascii=False,
            )
            benchmark_path = bench_handle.name

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as key_handle:
            key_handle.write("1: A\n")
            key_path = key_handle.name

        try:
            result = run_retrieval_benchmark(
                benchmark_json_path=benchmark_path,
                answer_key_path=key_path,
                ask_fn=lambda _prompt: "RASPUNS: A",
            )
            self.assertEqual(result["dataset_total_count"], 2)
            self.assertEqual(result["evaluated_count"], 1)
            self.assertEqual(result["answer_key_coverage"], 0.5)
            self.assertEqual(result["global_score"], 0.5)
            self.assertEqual(result["global_exact_match_rate"], 0.5)
        finally:
            Path(benchmark_path).unlink(missing_ok=True)
            Path(key_path).unlink(missing_ok=True)

    def test_requires_single_answer_for_unique_types(self) -> None:
        self.assertTrue(_requires_single_answer("u.f.d.f.d. Febra ..."))
        self.assertTrue(_requires_single_answer("u.i.d.f.d. Temperatura ..."))
        self.assertTrue(_requires_single_answer("u.f.c.d. ORL ..."))
        self.assertTrue(_requires_single_answer("c.e. Urmatoarele afirmatii sunt corecte:"))
        self.assertTrue(_requires_single_answer("C.E. Urmatoarele afirmatii sunt adevarate:"))
        self.assertTrue(_requires_single_answer("care este exceptia dintre urmatoarele"))
        self.assertTrue(
            _requires_single_answer("Una falsă dintre cele date. Febra (se completează fraza corect enunțată)")
        )
        self.assertFalse(_requires_single_answer("R.I. starea de hidratare ..."))

    def test_run_retrieval_benchmark_retries_for_textual_single_answer_format(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as bench_handle:
            json.dump(
                [
                    {
                        "id": 528,
                        "intrebare": "una falsă dintre cele date, Febra se completează fraza corect enunțată",
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
            key_handle.write("528: D\n")
            key_path = key_handle.name

        calls: list[str] = []

        def fake_ask(prompt: str) -> str:
            calls.append(prompt)
            if len(calls) == 1:
                return "RASPUNS: A, B, C, E"
            return "RASPUNS: D"

        try:
            result = run_retrieval_benchmark(
                benchmark_json_path=benchmark_path,
                answer_key_path=key_path,
                ask_fn=fake_ask,
            )
            self.assertEqual(result["rows"][0]["predicted_answers"], ["D"])
            self.assertTrue(result["rows"][0]["single_answer_retry_used"])
            self.assertEqual(len(calls), 2)
        finally:
            Path(benchmark_path).unlink(missing_ok=True)
            Path(key_path).unlink(missing_ok=True)

    def test_run_retrieval_benchmark_retries_when_single_answer_returns_multiple(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".json", encoding="utf-8") as bench_handle:
            json.dump(
                [
                    {
                        "id": 527,
                        "intrebare": "u.f.d.f.d. Febra s.c.f.c.e.",
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
            key_handle.write("527: A\n")
            key_path = key_handle.name

        calls: list[str] = []

        def fake_ask(prompt: str) -> str:
            calls.append(prompt)
            if len(calls) == 1:
                return "RASPUNS: B, C, D, E"
            return "RASPUNS: A"

        try:
            result = run_retrieval_benchmark(
                benchmark_json_path=benchmark_path,
                answer_key_path=key_path,
                ask_fn=fake_ask,
            )
            self.assertEqual(result["rows"][0]["predicted_answers"], ["A"])
            self.assertTrue(result["rows"][0]["single_answer_retry_used"])
            self.assertEqual(len(calls), 2)
        finally:
            Path(benchmark_path).unlink(missing_ok=True)
            Path(key_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
