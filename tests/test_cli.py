from __future__ import annotations

import subprocess
import sys
import unittest

import run


class TestCLI(unittest.TestCase):
    def test_parser_contains_expected_commands(self) -> None:
        parser = run._build_parser()
        command_actions = [a for a in parser._actions if a.dest == "command"]
        self.assertEqual(len(command_actions), 1)
        choices = set(command_actions[0].choices.keys())
        self.assertSetEqual(choices, {"chat", "ingest", "eval"})

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


if __name__ == "__main__":
    unittest.main()

