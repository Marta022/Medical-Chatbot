from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from agent.reasoning import translator


class TestTranslator(unittest.TestCase):
    def test_translate_to_english(self) -> None:
        fake = MagicMock()
        fake.translate.return_value = "hello"
        with patch("agent.reasoning.translator.GoogleTranslator", return_value=fake):
            result = translator.translate_to_english("salut")
        self.assertEqual(result, "hello")

    def test_translate_to_romanian(self) -> None:
        fake = MagicMock()
        fake.translate.side_effect = ["buna", "ziua"]
        with patch("agent.reasoning.translator.GoogleTranslator", return_value=fake):
            result = translator.translate_to_romanian(["hello", "day"])
        self.assertEqual(result, ["buna", "ziua"])


if __name__ == "__main__":
    unittest.main()
