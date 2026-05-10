from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent.benchmarking.benchmark import (
    BENCHMARK_SYSTEM_PROMPT,
    _benchmark_rejection_reason,
    _benchmark_requires_single_answer,
    _build_benchmark_context_block,
    _build_grila_prompt,
    _build_option_queries,
    _extract_option_letters,
    _is_uascce_question,
    _requires_single_answer,
    _rerank_benchmark_hits,
    load_retrieval_answer_key,
    load_retrieval_benchmark_items,
    run_retrieval_benchmark,
)
from models import RetrievalHit


class TestBenchmark(unittest.TestCase):
    def test_build_grila_prompt_adds_sequence_reasoning_for_fdu_chain_questions(self) -> None:
        prompt = _build_grila_prompt(
            {
                "id": 523,
                "intrebare": "F.d.u. Evenimente legate de febra. Care este lantul temporal corect?",
                "choices": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
            }
        )
        self.assertIn("Reconstruieste mai intai ordinea corecta", prompt)
        self.assertIn("varianta corecta unica", prompt)

    def test_build_grila_prompt_mentions_cdd_semantics(self) -> None:
        prompt = _build_grila_prompt(
            {
                "id": 540,
                "intrebare": "C.d.d. Nu face parte dintre categoriile de persoane cele mai expuse la soc termic.",
                "choices": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
            }
        )
        self.assertIn("Pentru C.d.d.", prompt)

    def test_build_grila_prompt_for_uascce_requires_false_letters_in_answer(self) -> None:
        prompt = _build_grila_prompt(
            {
                "id": 541,
                "intrebare": "u.a.s.c.c.e. Temperatura corporala normala si patologica.",
                "choices": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
            }
        )
        self.assertIn("u.a.s.c.c.e. cere literele variantelor FALSE/INCORECTE", prompt)
        self.assertIn("ANSWER: <doar literele variantelor FALSE/INCORECTE", prompt)

    def test_build_grila_prompt_for_ce_requires_exception_false_letter(self) -> None:
        prompt = _build_grila_prompt(
            {
                "id": 590,
                "intrebare": "Sindromul febril poate include, c.e.",
                "choices": {"A": "falsa", "B": "adevarata", "C": "adevarata", "D": "d", "E": "e"},
            }
        )
        self.assertIn("intrebare de exceptie", prompt)
        self.assertIn("ANSWER: <o singura litera, varianta FALSE/EXCEPTIA>", prompt)

    def test_uascce_detection_handles_trailing_dot_and_combined_ri_marker(self) -> None:
        question = "R.I. Temperatura corporala normala si patologica, u.a.s.c.c.e."
        self.assertTrue(_is_uascce_question(question))
        self.assertFalse(_requires_single_answer(question))

    def test_benchmark_system_prompt_is_exam_specific(self) -> None:
        self.assertIn("multiple-choice benchmark items", BENCHMARK_SYSTEM_PROMPT)
        self.assertIn("derive the correct order or mapping", BENCHMARK_SYSTEM_PROMPT)

    def test_benchmark_requires_single_answer_for_sequence_options(self) -> None:
        item = {
            "id": 523,
            "intrebare": "R.I. Care este lantul temporal corect?",
            "choices": {
                "A": "a-c-d-b-e",
                "B": "b-e-d-c-a",
                "C": "c-e-a-d-b",
                "D": "d-b-e-a-c",
                "E": "e-c-a-b-d",
            },
        }
        self.assertTrue(_benchmark_requires_single_answer(item))

    def test_benchmark_requires_single_answer_for_mapping_options(self) -> None:
        item = {
            "id": 529,
            "intrebare": "R.I. Care sunt asocierile corecte?",
            "choices": {
                "A": "a-1, b-2, c-3",
                "B": "a-1, b-3, c-2",
                "C": "a-2, b-1, c-3",
                "D": "a-3, b-1, c-2",
                "E": "a-3, b-2, c-1",
            },
        }
        self.assertTrue(_benchmark_requires_single_answer(item))

    def test_benchmark_requires_single_answer_for_scfce_fragments(self) -> None:
        item = {
            "id": 527,
            "intrebare": "U.f.d.f.d. Febra s.c.f.c.e.",
            "choices": {
                "A": "Procesele fiziologice prin care caldura este conservata (vasodilatatie).",
                "B": "sau produsa (termogeneza musculara, hepatica etc.)",
                "C": "continua pana cand",
                "D": "temperatura sangelui care iriga neuronii hipotalamici",
                "E": "corespunde noului nivel de referinta al termostatului",
            },
        }
        self.assertTrue(_benchmark_requires_single_answer(item))

    def test_benchmark_requires_single_answer_for_fdd_and_cdd(self) -> None:
        self.assertTrue(
            _benchmark_requires_single_answer(
                {
                    "id": 1,
                    "intrebare": "F.d.d. Care este inlantuirea temporala cauzala corecta?",
                    "choices": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
                }
            )
        )
        self.assertTrue(
            _benchmark_requires_single_answer(
                {
                    "id": 2,
                    "intrebare": "C.d.d. Nu face parte dintre categoriile expuse.",
                    "choices": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
                }
            )
        )

    def test_build_option_queries_emits_question_and_each_option(self) -> None:
        item = {
            "id": 1,
            "intrebare": "Q",
            "choices": {"A": "a", "B": "b", "C": "c", "D": "", "E": "e"},
        }
        queries = _build_option_queries(item)
        self.assertEqual(queries[0], "Q")
        self.assertIn("Optiunea A: a", queries[1])
        self.assertIn("Optiunea B: b", queries[2])
        self.assertEqual(len(queries), 5)

    def test_rerank_benchmark_hits_prefers_option_aligned_hit(self) -> None:
        item = {
            "id": 530,
            "intrebare": "Care sunt asocierile corecte?",
            "choices": {
                "A": "a-1, b-2, c-3",
                "B": "a-1, b-3, c-2",
                "C": "a-2, b-1, c-3",
                "D": "a-2, b-3, c-1",
                "E": "a-3, b-1, c-2",
            },
        }
        hits = [
            RetrievalHit(title="generic", text="febra si temperatura", score=0.95, source="unit"),
            RetrievalHit(
                title="mapping",
                text="a-1 b-2 c-3 tremuraturi ghemuire dezvelire",
                score=0.8,
                source="unit",
            ),
        ]
        ranked = _rerank_benchmark_hits(item, hits, top_k=1)
        self.assertEqual(ranked[0].title, "mapping")

    def test_build_benchmark_context_block_is_plain_context(self) -> None:
        context = _build_benchmark_context_block(
            {
                "id": 1,
                "intrebare": "Q",
                "choices": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
            },
            [
                RetrievalHit(
                    title="t",
                    text="context body",
                    score=0.9,
                    source="pdf",
                    source_file="doc.md",
                    page=2,
                    section="Febra",
                    chunk_id="c1",
                )
            ],
        )
        self.assertIn("Context benchmark relevant:", context)
        self.assertIn("source_file=doc.md", context)
        self.assertNotIn("Most similar chunks:", context)

    def test_benchmark_rejection_reason_forbidden_reasoning(self) -> None:
        item = {
            "id": 523,
            "intrebare": "F.d.u. Care este lantul temporal corect?",
            "choices": {
                "A": "a-c-d-b-e",
                "B": "b-e-d-c-a",
                "C": "c-e-a-d-b",
                "D": "d-b-e-a-c",
                "E": "e-c-a-b-d",
            },
        }
        self.assertEqual(
            _benchmark_rejection_reason(item, "RASPUNS: A\nbazat pe cunostinte generale"),
            "forbidden_reasoning",
        )

    def test_benchmark_rejection_reason_requires_variant_to_match_answer(self) -> None:
        item = {
            "id": 523,
            "intrebare": "F.d.u. Care este lantul temporal corect?",
            "choices": {
                "A": "a-c-d-b-e",
                "B": "b-e-d-c-a",
                "C": "c-e-a-d-b",
                "D": "d-b-e-a-c",
                "E": "e-c-a-b-d",
            },
        }
        self.assertEqual(
            _benchmark_rejection_reason(item, "ORDINE: e-c-a-b-d\nVARIANTA: E\nRASPUNS: C"),
            "answer_variant_mismatch",
        )

    def test_benchmark_rejection_reason_requires_sequence_variant_to_match_option_text(
        self,
    ) -> None:
        item = {
            "id": 524,
            "intrebare": "F.d.u. Care este lantul temporal corect?",
            "choices": {
                "A": "a-d-c-e-b",
                "B": "b-e-c-a-d",
                "C": "c-a-e-b-d",
                "D": "d-e-a-c-b",
                "E": "e-a-c-d-b",
            },
        }
        self.assertEqual(
            _benchmark_rejection_reason(item, "ORDINE: c-a-e-b-d\nVARIANTA: A\nRASPUNS: A"),
            "derived_value_variant_mismatch",
        )

    def test_benchmark_rejection_reason_requires_mapping_variant_to_match_option_text(self) -> None:
        item = {
            "id": 529,
            "intrebare": "R.I. Care sunt asocierile corecte?",
            "choices": {
                "A": "a-1, b-2, c-3",
                "B": "a-1, b-3, c-2",
                "C": "a-2, b-1, c-3",
                "D": "a-3, b-1, c-2",
                "E": "a-3, b-2, c-1",
            },
        }
        self.assertEqual(
            _benchmark_rejection_reason(item, "ASOCIERI: a-2, b-1, c-3\nVARIANTA: A\nRASPUNS: A"),
            "derived_value_variant_mismatch",
        )

    def test_benchmark_rejection_reason_accepts_multi_answer_statuses_that_match(self) -> None:
        item = {
            "id": 521,
            "intrebare": "u.a.s.c.c.e. Q",
            "choices": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
        }
        response = (
            "STATUT_A: ADEVARAT\nSTATUT_B: FALS\nSTATUT_C: ADEVARAT\n"
            "STATUT_D: FALS\nSTATUT_E: FALS\nRASPUNS: B, D, E"
        )
        self.assertIsNone(_benchmark_rejection_reason(item, response))

    def test_benchmark_rejection_reason_handles_uascce_with_trailing_dot(self) -> None:
        item = {
            "id": 521,
            "intrebare": "Temperatura corporala normala si patologica, u.a.s.c.c.e.",
            "choices": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
        }
        response = (
            "STATUS_A: FALSE\nSTATUS_B: TRUE\nSTATUS_C: FALSE\n"
            "STATUS_D: FALSE\nSTATUS_E: TRUE\nANSWER: A,C,D"
        )
        self.assertIsNone(_benchmark_rejection_reason(item, response))

    def test_benchmark_rejection_reason_rejects_all_false_uascce_with_trailing_dot(self) -> None:
        item = {
            "id": 521,
            "intrebare": "Temperatura corporala normala si patologica, u.a.s.c.c.e.",
            "choices": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
        }
        response = (
            "STATUS_A: FALSE\nSTATUS_B: FALSE\nSTATUS_C: FALSE\n"
            "STATUS_D: FALSE\nSTATUS_E: FALSE\nANSWER: A,B,C,D,E"
        )
        self.assertEqual(_benchmark_rejection_reason(item, response), "all_options_selected")

    def test_benchmark_rejection_reason_rejects_true_answer_for_ce_exception(self) -> None:
        item = {
            "id": 590,
            "intrebare": "Manifestarile neuropsihice pot include, c.e.:",
            "choices": {"A": "exceptie", "B": "corect", "C": "corect", "D": "corect", "E": "corect"},
        }
        response = (
            "STATUS_A: FALSE\nSTATUS_B: TRUE\nSTATUS_C: TRUE\n"
            "STATUS_D: TRUE\nSTATUS_E: TRUE\nANSWER: B"
        )
        self.assertEqual(_benchmark_rejection_reason(item, response), "status_answer_mismatch")

    def test_benchmark_rejection_reason_accepts_false_answer_for_uce_exception(self) -> None:
        item = {
            "id": 592,
            "intrebare": "Efectele negative ale febrei se afla u.c.e.:",
            "choices": {"A": "corect", "B": "corect", "C": "corect", "D": "corect", "E": "exceptie"},
        }
        response = (
            "STATUS_A: TRUE\nSTATUS_B: TRUE\nSTATUS_C: TRUE\n"
            "STATUS_D: TRUE\nSTATUS_E: FALSE\nANSWER: E"
        )
        self.assertIsNone(_benchmark_rejection_reason(item, response))

    def test_benchmark_rejection_reason_rejects_all_true_multi_answer(self) -> None:
        item = {
            "id": 526,
            "intrebare": "R.I. Febra si frisonul",
            "choices": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
        }
        response = (
            "STATUT_A: ADEVARAT\nSTATUT_B: ADEVARAT\nSTATUT_C: ADEVARAT\n"
            "STATUT_D: ADEVARAT\nSTATUT_E: ADEVARAT\nRASPUNS: A,B,C,D,E"
        )
        self.assertEqual(_benchmark_rejection_reason(item, response), "all_options_selected")

    def test_extract_option_letters_falls_back_to_leading_letter_for_hyphenated_option_text(
        self,
    ) -> None:
        self.assertEqual(_extract_option_letters("RASPUNS: e-c-a-b-d"), {"E"})

    def test_extract_option_letters_uses_answer_segment_only(self) -> None:
        raw_response = (
            "RASPUNS: C,D\n\n"
            "Most similar chunks:\n"
            "A) fragment din context\n"
            "B) alt fragment"
        )
        self.assertEqual(_extract_option_letters(raw_response), {"C", "D"})

    def test_load_retrieval_answer_key_supports_multiple_answers(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".txt", encoding="utf-8"
        ) as handle:
            handle.write("521: A,C\n522: B\n")
            key_path = handle.name
        try:
            answer_key = load_retrieval_answer_key(key_path)
            self.assertEqual(answer_key[521], {"A", "C"})
            self.assertEqual(answer_key[522], {"B"})
        finally:
            Path(key_path).unlink(missing_ok=True)

    def test_run_retrieval_benchmark_computes_set_metrics(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as bench_handle:
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

        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".txt", encoding="utf-8"
        ) as key_handle:
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
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as handle:
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
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as handle:
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
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as bench_handle:
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

        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".txt", encoding="utf-8"
        ) as key_handle:
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
        self.assertTrue(_requires_single_answer("F.d.u. Care este lantul temporal corect?"))
        self.assertTrue(_requires_single_answer("c.e. Urmatoarele afirmatii sunt corecte:"))
        self.assertTrue(_requires_single_answer("C.E. Urmatoarele afirmatii sunt adevarate:"))
        self.assertTrue(_requires_single_answer("u.c.e. Printre efecte se afla:"))
        self.assertTrue(_requires_single_answer("care este exceptia dintre urmatoarele"))
        self.assertTrue(
            _requires_single_answer(
                "Una falsă dintre cele date. Febra (se completează fraza corect enunțată)"
            )
        )
        self.assertFalse(
            _requires_single_answer("Temperatura corporala normala si patologica, u.a.s.c.c.e.")
        )
        self.assertFalse(_requires_single_answer("R.I. starea de hidratare ..."))

    def test_run_retrieval_benchmark_retries_for_textual_single_answer_format(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as bench_handle:
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

        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".txt", encoding="utf-8"
        ) as key_handle:
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
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as bench_handle:
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

        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".txt", encoding="utf-8"
        ) as key_handle:
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

    def test_run_retrieval_benchmark_includes_retrieved_chunks_in_rows(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as bench_handle:
            json.dump(
                [
                    {
                        "id": 610,
                        "intrebare": "Q chunk",
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

        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".txt", encoding="utf-8"
        ) as key_handle:
            key_handle.write("610: A\n")
            key_path = key_handle.name

        retrieval_hits = [
            RetrievalHit(
                title="chunk-title",
                text="chunk body",
                score=0.9321,
                source="pdf",
                source_file="doc.md",
                page=7,
                section="Sectiune",
                chunk_id="chunk-1",
            )
        ]

        try:
            with patch("rag.retrieval.retriever.retrieve_top_similar") as retrieve_mock:
                with patch("llm.llm_router.llm_ask_request") as llm_mock:
                    retrieve_mock.return_value.hits = retrieval_hits
                    llm_mock.return_value.content = "RASPUNS: A"
                    result = run_retrieval_benchmark(
                        benchmark_json_path=benchmark_path,
                        answer_key_path=key_path,
                    )

            self.assertEqual(result["rows"][0]["predicted_answers"], ["A"])
            self.assertEqual(len(result["rows"][0]["retrieved_chunks"]), 1)
            self.assertEqual(result["rows"][0]["retrieved_chunks"][0]["chunk_id"], "chunk-1")
            self.assertEqual(result["rows"][0]["retrieved_chunks"][0]["text"], "chunk body")
            self.assertEqual(result["rows"][0]["retrieved_chunks"][0]["score"], 0.9321)
        finally:
            Path(benchmark_path).unlink(missing_ok=True)
            Path(key_path).unlink(missing_ok=True)

    def test_run_retrieval_benchmark_keeps_last_rejected_response_and_reason(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as bench_handle:
            json.dump(
                [
                    {
                        "id": 611,
                        "intrebare": "R.I. Q reject",
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

        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".txt", encoding="utf-8"
        ) as key_handle:
            key_handle.write("611: A\n")
            key_path = key_handle.name

        try:
            with patch("rag.retrieval.retriever.retrieve_top_similar") as retrieve_mock:
                with patch("llm.llm_router.llm_ask_request") as llm_mock:
                    retrieve_mock.return_value.hits = []
                    llm_mock.return_value.content = (
                        "STATUT_A: ADEVARAT\nSTATUT_B: FALS\nSTATUT_C: FALS\n"
                        "STATUT_D: FALS\nSTATUT_E: FALS\nRASPUNS: B"
                    )
                    result = run_retrieval_benchmark(
                        benchmark_json_path=benchmark_path,
                        answer_key_path=key_path,
                    )

            self.assertEqual(result["rows"][0]["predicted_answers"], ["B"])
            self.assertEqual(result["rows"][0]["raw_response"], llm_mock.return_value.content)
            self.assertEqual(result["rows"][0]["rejection_reason"], "status_answer_mismatch")
        finally:
            Path(benchmark_path).unlink(missing_ok=True)
            Path(key_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
