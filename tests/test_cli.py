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
        self.assertSetEqual(choices, {"chat", "ingest", "eval", "toc-export"})
        ingest_parser = command_actions[0].choices["ingest"]
        ingest_option_dests = {action.dest for action in ingest_parser._actions}
        self.assertIn("chunking_strategy", ingest_option_dests)
        self.assertIn("pdf_path", ingest_option_dests)
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
        toc_option_dests = {action.dest for action in command_actions[0].choices["toc-export"]._actions}
        self.assertIn("pdf_path", toc_option_dests)
        self.assertIn("output_json_path", toc_option_dests)
        self.assertIn("toc_page_index", toc_option_dests)
        self.assertIn("expected_columns", toc_option_dests)
        self.assertIn("page_offset", toc_option_dests)
        self.assertIn("page_validation_window", toc_option_dests)
        self.assertIn("require_title_hint", toc_option_dests)
        self.assertIn("min_native_text_chars", toc_option_dests)
        self.assertIn("use_pp_structure_fallback", toc_option_dests)
        self.assertIn("toc_entries_json_path", toc_option_dests)

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
        self.assertIn("eval", completed.stdout)
        self.assertIn("toc-export", completed.stdout)

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

    def test_toc_export_command_writes_sections(self) -> None:
        argv = [
            "run.py",
            "toc-export",
            "--pdf-path",
            "data/dataset/DORIN-CURS_SEM2_searchable.pdf",
            "--output-json-path",
            "data/dataset/out.json",
            "--toc-page-index",
            "1",
            "--expected-columns",
            "2",
            "--page-offset",
            "0",
            "--page-validation-window",
            "2",
            "--require-title-hint",
            "--min-native-text-chars",
            "120",
            "--use-pp-structure-fallback",
            "--toc-entries-json-path",
            "data/dataset/out_toc_entries.json",
        ]
        with patch.object(sys, "argv", argv):
            with patch(
                "run.export_toc_sections_with_validation_to_json",
                return_value=([], []),
            ) as export_mock:
                run.main()

        export_mock.assert_called_once()
        self.assertEqual(export_mock.call_args.args[0], "data/dataset/DORIN-CURS_SEM2_searchable.pdf")


if __name__ == "__main__":
    unittest.main()
