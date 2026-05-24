from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import run


class TestCLI(unittest.TestCase):
    def test_parser_contains_expected_commands(self) -> None:
        parser = run._build_parser()
        command_actions = [a for a in parser._actions if a.dest == "command"]
        self.assertEqual(len(command_actions), 1)
        choices = set(command_actions[0].choices.keys())
        self.assertSetEqual(choices, {"chat", "ingest", "extract-markdown", "eval"})
        ingest_parser = command_actions[0].choices["ingest"]
        ingest_option_dests = {action.dest for action in ingest_parser._actions}
        self.assertIn("chunking_strategy", ingest_option_dests)
        self.assertIn("pdf_path", ingest_option_dests)
        self.assertIn("markdown_path", ingest_option_dests)
        self.assertIn("skip_pdf_ingest", ingest_option_dests)
        self.assertIn("pdf_only", ingest_option_dests)
        self.assertIn("quality_report", ingest_option_dests)
        self.assertIn("quality_report_path", ingest_option_dests)
        self.assertIn("quality_keyword", ingest_option_dests)
        self.assertIn("quality_keyword_limit", ingest_option_dests)
        chat_option_dests = {action.dest for action in command_actions[0].choices["chat"]._actions}
        self.assertIn("retrieval_mode", chat_option_dests)
        self.assertIn("graph_depth", chat_option_dests)
        self.assertIn("vector_weight", chat_option_dests)
        self.assertIn("graph_weight", chat_option_dests)
        extract_option_dests = {
            action.dest for action in command_actions[0].choices["extract-markdown"]._actions
        }
        self.assertIn("pdf_path", extract_option_dests)
        self.assertIn("start_page", extract_option_dests)
        self.assertIn("output_dir", extract_option_dests)
        self.assertIn("max_pages_per_run", extract_option_dests)
        self.assertIn("provider", extract_option_dests)
        eval_option_dests = {action.dest for action in command_actions[0].choices["eval"]._actions}
        self.assertIn("benchmark", eval_option_dests)
        self.assertIn("benchmark_json_path", eval_option_dests)
        self.assertIn("answer_key_path", eval_option_dests)
        self.assertIn("benchmark_top_k", eval_option_dests)
        self.assertIn("benchmark_limit", eval_option_dests)
        self.assertIn("benchmark_use_guardrail", eval_option_dests)

    def test_help_command_smoke(self) -> None:
        completed = subprocess.run(
            [sys.executable, "run.py", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("chat", completed.stdout)
        self.assertIn("ingest", completed.stdout)
        self.assertIn("extract-markdown", completed.stdout)
        self.assertIn("eval", completed.stdout)

    def test_eval_command_smoke(self) -> None:
        completed = subprocess.run(
            [sys.executable, "run.py", "eval"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("passed", completed.stdout)
        self.assertIn("score", completed.stdout)

    def test_chat_command_passes_graph_policy_filters(self) -> None:
        argv = [
            "run.py",
            "chat",
            "--top-k",
            "2",
            "--retrieval-mode",
            "hybrid",
            "--graph-depth",
            "2",
            "--vector-weight",
            "1.0",
            "--graph-weight",
            "0.5",
        ]
        with patch.object(sys, "argv", argv):
            with patch("run.ensure_startup_valid"):
                with patch("run.run_chat_loop") as chat_mock:
                    run.main()

        chat_mock.assert_called_once()
        kwargs = chat_mock.call_args.kwargs
        self.assertEqual(kwargs["top_k"], 2)
        self.assertEqual(kwargs["filters"]["__retrieval_mode"], "hybrid")
        self.assertEqual(kwargs["filters"]["__graph_depth"], "2")

    def test_extract_markdown_command_passes_runtime_controls(self) -> None:
        argv = [
            "run.py",
            "extract-markdown",
            "--pdf-path",
            "data/dataset/DORIN-CURS_SEM2_searchable.pdf",
            "--start-page",
            "6",
            "--end-page",
            "8",
            "--output-dir",
            "output",
            "--max-pages-per-run",
            "2",
            "--provider",
            "openai",
        ]
        with patch.object(sys, "argv", argv):
            with patch("run.ensure_startup_valid"):
                with patch(
                    "run.extract_pdf_to_markdown", return_value={"pages_processed": 2}
                ) as extract_mock:
                    run.main()

        extract_mock.assert_called_once()
        kwargs = extract_mock.call_args.kwargs
        self.assertEqual(kwargs["pdf_path"], "data/dataset/DORIN-CURS_SEM2_searchable.pdf")
        self.assertEqual(kwargs["start_page"], 6)
        self.assertEqual(kwargs["end_page"], 8)
        self.assertEqual(kwargs["output_dir"], "output")
        self.assertEqual(kwargs["max_pages_per_run"], 2)
        self.assertEqual(kwargs["provider"], "openai")

    def test_ingest_command_accepts_direct_markdown_path(self) -> None:
        argv = [
            "run.py",
            "ingest",
            "--markdown-path",
            "output/document.md",
            "--pdf-only",
        ]
        with patch.object(sys, "argv", argv):
            with patch("run.ensure_startup_valid"):
                with patch("run.ingest", return_value=7) as ingest_mock:
                    run.main()

        ingest_mock.assert_called_once()
        kwargs = ingest_mock.call_args.kwargs
        self.assertEqual(kwargs["pdf_paths"], ["output/document.md"])
        self.assertTrue(kwargs["include_structured_sources"] is False)

    def test_eval_benchmark_disables_guardrail_by_default(self) -> None:
        argv = ["run.py", "eval", "--benchmark"]
        with patch.object(sys, "argv", argv):
            with patch("run.ensure_startup_valid"):
                with patch(
                    "run.run_retrieval_benchmark",
                    return_value={"evaluated_count": 0, "aggregate": {}},
                ) as benchmark_mock:
                    run.main()

        benchmark_mock.assert_called_once()
        self.assertFalse(benchmark_mock.call_args.kwargs["use_guardrail"])

    def test_eval_benchmark_can_enable_guardrail_via_flag(self) -> None:
        argv = ["run.py", "eval", "--benchmark", "--benchmark-use-guardrail"]
        with patch.object(sys, "argv", argv):
            with patch("run.ensure_startup_valid"):
                with patch(
                    "run.run_retrieval_benchmark",
                    return_value={"evaluated_count": 0, "aggregate": {}},
                ) as benchmark_mock:
                    run.main()

        benchmark_mock.assert_called_once()
        self.assertTrue(benchmark_mock.call_args.kwargs["use_guardrail"])

    def test_next_benchmark_output_path_uses_anthropic_model_suffix(self) -> None:
        settings = replace(
            run.SETTINGS,
            llm_provider="anthropic",
            anthropic_model="claude-sonnet-4-20250514",
            qwen_model="qwen3.5",
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(run, "SETTINGS", settings):
                with patch("run.Path", wraps=Path) as path_mock:
                    path_mock.side_effect = lambda value: Path(temp_dir) / value
                    output_path = run._next_benchmark_output_path()

        self.assertTrue(output_path.endswith("output_v1_claude-sonnet-4-20250514.txt"))

    def test_eval_benchmark_writes_json_output_file(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, suffix=".json", encoding="utf-8"
        ) as handle:
            output_path = handle.name
        Path(output_path).unlink(missing_ok=True)

        argv = ["run.py", "eval", "--benchmark", "--benchmark-output", output_path]
        with patch.object(sys, "argv", argv):
            with patch("run.ensure_startup_valid"):
                with patch(
                    "run.run_retrieval_benchmark",
                    return_value={"evaluated_count": 1, "aggregate": {"macro_f1": 1.0}},
                ):
                    run.main()

        try:
            saved = json.loads(Path(output_path).read_text(encoding="utf-8"))
            self.assertEqual(saved["evaluated_count"], 1)
            self.assertEqual(saved["aggregate"]["macro_f1"], 1.0)
        finally:
            Path(output_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
