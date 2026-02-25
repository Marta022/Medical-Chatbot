from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from rag.chunking.load_documents import load_medical_items
from rag.chunking.strategies import (
    chunk_text,
    section_chunks,
    sentence_chunks,
    split_sentences,
    window_chunks,
)


class TestChunking(unittest.TestCase):
    def test_sentence_and_window_chunks(self) -> None:
        text = "A. B? C! D. E."
        sentences = split_sentences(text)
        self.assertEqual(len(sentences), 5)
        self.assertEqual(sentence_chunks(text, max_sentences=2)[0], "A. B?")
        self.assertTrue(window_chunks(text, window_size=2, stride=1))

    def test_section_chunks(self) -> None:
        text = "Line1\n\nLine2\nLine3"
        chunks = section_chunks(text)
        self.assertEqual(chunks, ["Line1", "Line2", "Line3"])

    def test_chunk_text_invalid_strategy(self) -> None:
        with self.assertRaises(ValueError):
            chunk_text("test", strategy="unknown")

    def test_load_documents_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "data.json"
            csv_path = Path(temp_dir) / "data.csv"

            json_path.write_text(json.dumps({"bad": "data"}), encoding="utf-8")
            csv_path.write_text("disease,symptoms\nflu,cure", encoding="utf-8")

            with self.assertRaises(ValueError):
                load_medical_items(str(json_path), str(csv_path))


if __name__ == "__main__":
    unittest.main()
