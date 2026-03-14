from __future__ import annotations

import subprocess
import sys
import unittest
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
                with patch("run.extract_pdf_to_markdown", return_value={"pages_processed": 2}) as extract_mock:
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


if __name__ == "__main__":
    unittest.main()
