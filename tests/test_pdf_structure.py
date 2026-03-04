from __future__ import annotations

import unittest
from unittest.mock import patch

from rag.chunking.load_documents import (
    _chunk_id_for,
    _decode_pdf_literal,
    load_pdf_chunks,
    parse_pdf_to_structured_chunks,
    profile_pdf_structure,
)


class TestPdfStructure(unittest.TestCase):
    def test_decode_pdf_literal_handles_escapes(self) -> None:
        value = r"Capitolul\0401\040\(Introducere\)\nLinie"
        decoded = _decode_pdf_literal(value)
        self.assertIn("Capitolul 1", decoded)
        self.assertIn("(Introducere)", decoded)
        self.assertIn("\n", decoded)

    def test_chunk_id_is_deterministic(self) -> None:
        first = _chunk_id_for("a.pdf", 2, "cap", "sec", 1, "sample text")
        second = _chunk_id_for("a.pdf", 2, "cap", "sec", 1, "sample text")
        third = _chunk_id_for("a.pdf", 3, "cap", "sec", 1, "sample text")
        self.assertEqual(first, second)
        self.assertNotEqual(first, third)

    def test_parse_pdf_to_structured_chunks_extracts_metadata(self) -> None:
        pages = [
            "\n".join(
                [
                    "CAPITOLUL 1 Introducere",
                    "1.1 Anatomie",
                    "Inima este un organ vital.",
                    "1. Durere toracica",
                    "2. Dispnee",
                ]
            )
        ]
        with patch("rag.chunking.load_documents.extract_pdf_pages", return_value=pages):
            chunks = parse_pdf_to_structured_chunks("DORIN-CURS_SEM2_searchable.pdf")

        self.assertGreaterEqual(len(chunks), 2)
        self.assertEqual(chunks[0].source_file, "DORIN-CURS_SEM2_searchable.pdf")
        self.assertEqual(chunks[0].page, 1)
        self.assertEqual(chunks[0].chapter, "CAPITOLUL 1 Introducere")
        self.assertEqual(chunks[0].section, "1.1 Anatomie")
        self.assertTrue(any(chunk.is_list for chunk in chunks))
        self.assertTrue(all(chunk.chunk_id for chunk in chunks))

    def test_profile_pdf_structure_summarizes_chunks(self) -> None:
        pages = [
            "\n".join(
                [
                    "CAPITOLUL 2 Cardiologie",
                    "2.1 Evaluare clinica",
                    "Pacientul prezinta simptome diverse.",
                ]
            ),
            "\n".join(
                [
                    "2.2 Tratament",
                    "- Administrare medicatie",
                    "- Reevaluare periodica",
                ]
            ),
        ]
        with patch("rag.chunking.load_documents.extract_pdf_pages", return_value=pages):
            profile = profile_pdf_structure("DORIN_GENERALA_CARDIOVASCULARA-RESPIRATORIE-DISESTIVA.CV01.pdf")

        self.assertEqual(profile["source_file"], "DORIN_GENERALA_CARDIOVASCULARA-RESPIRATORIE-DISESTIVA.CV01.pdf")
        self.assertEqual(profile["pages_detected"], 2)
        self.assertGreater(profile["chunk_count"], 0)
        self.assertGreaterEqual(profile["list_chunk_count"], 1)
        self.assertIn("CAPITOLUL 2 Cardiologie", profile["chapters_detected"])

    def test_load_pdf_chunks_section_returns_base_chunks(self) -> None:
        pages = [
            "\n".join(
                [
                    "CAPITOLUL 1",
                    "1.1 Sectiune",
                    "Text simplu de test.",
                ]
            )
        ]
        with patch("rag.chunking.load_documents.extract_pdf_pages", return_value=pages):
            section_chunks = load_pdf_chunks(
                "DORIN-CURS_SEM2_searchable.pdf",
                chunking_strategy="section",
            )
            semantic_chunks = load_pdf_chunks(
                "DORIN-CURS_SEM2_searchable.pdf",
                chunking_strategy="semantic",
                semantic_chunk_max_chars=50,
                semantic_use_llamaindex=False,
            )

        self.assertGreaterEqual(len(section_chunks), 1)
        self.assertGreaterEqual(len(semantic_chunks), 1)
        self.assertTrue(all(chunk.page == 1 for chunk in semantic_chunks))
        self.assertTrue(all(chunk.source_file == "DORIN-CURS_SEM2_searchable.pdf" for chunk in semantic_chunks))
        self.assertTrue(all(chunk.chunk_id for chunk in semantic_chunks))


if __name__ == "__main__":
    unittest.main()
