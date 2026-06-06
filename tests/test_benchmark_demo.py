from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run_benchmark_demo
from models import LLMResponse, RetrievalHit, RetrievalResult


class TestBenchmarkDemo(unittest.TestCase):
    def test_run_demo_runs_first_grid_and_writes_output(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as handle:
            output_path = handle.name
        Path(output_path).unlink(missing_ok=True)

        try:
            with patch(
                "run_benchmark_demo.load_retrieval_benchmark_items",
                return_value=[
                    {
                        "id": 521,
                        "intrebare": "Q",
                        "choices": {"A": "a", "B": "b", "C": "c", "D": "d", "E": "e"},
                    }
                ],
            ):
                with patch(
                    "run_benchmark_demo.load_retrieval_answer_key",
                    return_value={521: {"A", "C", "D"}},
                ):
                    retrieval_result = RetrievalResult(
                        hits=[
                            RetrievalHit(
                                title="t",
                                text="chunk",
                                score=0.9,
                                source="pdf",
                                chunk_id="c1",
                            )
                        ],
                    )
                    with patch(
                        "rag.retrieval.retriever.retrieve_top_similar",
                        return_value=retrieval_result,
                    ) as retrieve_mock:
                        with patch(
                            "llm.llm_router.llm_ask_request",
                            return_value=LLMResponse(
                                content=(
                                    "STATUS_A: FALSE\nSTATUS_B: TRUE\nSTATUS_C: FALSE\n"
                                    "STATUS_D: FALSE\nSTATUS_E: TRUE\nANSWER: A,C,D"
                                ),
                                provider="openai",
                            ),
                        ):
                            payload = run_benchmark_demo.run_demo(output=output_path)

            self.assertGreaterEqual(retrieve_mock.call_count, 1)
            saved = json.loads(Path(output_path).read_text(encoding="utf-8"))
            self.assertEqual(saved["evaluated_count"], 1)
            self.assertTrue(saved["rows"][0]["exact_match"])
            self.assertEqual(payload["rows"][0]["id"], 521)
        finally:
            Path(output_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
