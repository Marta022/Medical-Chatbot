from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from models.contracts import PdfStructuredChunk
from rag.chunking.load_documents import load_medical_items
from rag.chunking.strategies import (
    chunk_structured_chunks,
    chunk_text,
    section_chunks,
    semantic_chunks,
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
        self.assertEqual(chunks, ["Line1", "Line2 Line3"])

    def test_section_chunks_preserve_markdown_heading_and_list_blocks(self) -> None:
        text = "\n".join(
            [
                "# Capitol",
                "Paragraf pe doua",
                "linii",
                "",
                "- item 1",
                "- item 2",
            ]
        )
        chunks = section_chunks(text)
        self.assertEqual(chunks[0], "# Capitol")
        self.assertEqual(chunks[1], "Paragraf pe doua linii")
        self.assertIn("- item 1", chunks[2])
        self.assertIn("- item 2", chunks[2])

    def test_chunk_text_invalid_strategy(self) -> None:
        with self.assertRaises(ValueError):
            chunk_text("test", strategy="unknown")

    def test_semantic_chunks_preserve_numbered_list_block(self) -> None:
        text = "\n".join(
            [
                "Semne clinice importante.",
                "1. Durere toracica persistenta",
                "2. Dispnee de efort",
                "3. Palpitatii frecvente",
                "Tratamentul depinde de context.",
            ]
        )
        with patch(
            "rag.chunking.strategies._llamaindex_semantic_chunks",
            return_value=[
                "Semne clinice importante.",
                "1. Durere toracica persistenta\n2. Dispnee de efort\n3. Palpitatii frecvente",
                "Tratamentul depinde de context.",
            ],
        ):
            chunks = semantic_chunks(text, max_chars=300, use_llamaindex=True)
        merged = "\n".join(chunks)
        self.assertIn("1. Durere toracica persistenta", merged)
        self.assertIn("2. Dispnee de efort", merged)
        self.assertIn("3. Palpitatii frecvente", merged)
        self.assertTrue(any("1. Durere toracica persistenta" in chunk for chunk in chunks))

    def test_chunk_text_semantic_raises_without_llamaindex(self) -> None:
        text = "Paragraf introductiv.\n\n- item 1\n- item 2"
        with patch("rag.chunking.strategies._llamaindex_semantic_chunks", return_value=[]):
            with self.assertRaises(RuntimeError):
                chunk_text(
                    text,
                    strategy="semantic",
                    semantic_max_chars=80,
                    semantic_use_llamaindex=True,
                )

    def test_chunk_structured_chunks_keeps_metadata(self) -> None:
        base = PdfStructuredChunk(
            source_file="demo.pdf",
            page=4,
            chapter="CAPITOLUL 3",
            section="3.2 Tratament",
            chunk_id="abc123",
            text="Paragraf A. Paragraf B.\n1. Lista unu\n2. Lista doi",
            is_list=False,
        )
        with patch(
            "rag.chunking.strategies._llamaindex_semantic_chunks",
            return_value=["Paragraf A. Paragraf B.", "1. Lista unu 2. Lista doi"],
        ):
            chunks = chunk_structured_chunks(
                [base],
                strategy="semantic",
                semantic_max_chars=40,
                semantic_use_llamaindex=True,
            )
        self.assertGreaterEqual(len(chunks), 1)
        self.assertTrue(all(chunk.source_file == "demo.pdf" for chunk in chunks))
        self.assertTrue(all(chunk.page == 4 for chunk in chunks))
        self.assertTrue(all(chunk.chapter == "CAPITOLUL 3" for chunk in chunks))
        self.assertTrue(all(chunk.section == "3.2 Tratament" for chunk in chunks))
        self.assertTrue(all(chunk.chunk_id for chunk in chunks))

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
