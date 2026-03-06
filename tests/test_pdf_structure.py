from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from models.contracts import PdfStructuredChunk
from rag.chunking.load_documents import (
    _build_lines_from_positioned_fragments,
    _group_structured_chunks_for_semantic,
    _merge_page_lines,
    _chunk_id_for,
    _decode_pdf_literal,
    extract_pdf_pages,
    load_pdf_chunks,
    parse_pdf_to_structured_chunks,
    profile_pdf_structure,
)


class TestPdfStructure(unittest.TestCase):
    def test_extract_pdf_pages_recovers_unreadable_page_with_ocr(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "demo.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            with patch(
                "rag.chunking.load_documents._extract_pages_with_pymupdf",
                return_value={},
            ):
                with patch(
                    "rag.chunking.load_documents._fallback_extract_pdf_pages",
                    return_value=[],
                ):
                    with patch(
                        "rag.chunking.load_documents._extract_pages_with_rapidocr",
                        return_value={0: "Text OCR pagina"},
                    ) as ocr_mock:
                        pages = extract_pdf_pages(str(pdf_path))

        self.assertEqual(pages, ["Text OCR pagina"])
        ocr_mock.assert_called_once()

    def test_build_lines_from_positioned_fragments_reorders_two_columns(self) -> None:
        fragments = [
            (50.0, 700.0, "L1"),
            (50.0, 690.0, "L2"),
            (320.0, 700.0, "R1"),
            (320.0, 690.0, "R2"),
        ] * 3
        lines = _build_lines_from_positioned_fragments(fragments)
        self.assertGreaterEqual(len(lines), 4)
        self.assertTrue(lines[0].startswith("L1"))
        self.assertTrue(any(line.startswith("R1") for line in lines[-2:]))

    def test_merge_page_lines_joins_hyphenated_wrap(self) -> None:
        merged = _merge_page_lines(["emboliza-", "rea colesterolica.", "Titlu"])
        self.assertEqual(merged[0], "embolizarea colesterolica.")
        self.assertIn("Titlu", merged)

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

    def test_group_structured_chunks_for_semantic_merges_page_chapter_fragments(self) -> None:
        base_chunks = [
            PdfStructuredChunk(
                source_file="DORIN-CURS_SEM2_searchable.pdf",
                page=315,
                chapter="CAPITOLUL 9",
                section="GPLM, GSFS, GPM;",
                chunk_id="a1",
                text="de colesterol,",
                is_list=False,
            ),
            PdfStructuredChunk(
                source_file="DORIN-CURS_SEM2_searchable.pdf",
                page=315,
                chapter="CAPITOLUL 9",
                section="Boala",
                chunk_id="a2",
                text="emboliile cu colesterol provenite din placile ateromatoase",
                is_list=False,
            ),
        ]
        grouped = _group_structured_chunks_for_semantic(base_chunks, group_target_chars=500)
        self.assertEqual(len(grouped), 1)
        self.assertIn("de colesterol,", grouped[0].text)
        self.assertIn("emboliile cu colesterol", grouped[0].text)
        self.assertEqual(grouped[0].section, "multiple")

    def test_load_pdf_chunks_semantic_groups_before_rechunk(self) -> None:
        base_chunks = [
            PdfStructuredChunk(
                source_file="demo.pdf",
                page=1,
                chapter="CAPITOLUL 1",
                section="1.1 A",
                chunk_id="c1",
                text="fragment unu",
                is_list=False,
            ),
            PdfStructuredChunk(
                source_file="demo.pdf",
                page=1,
                chapter="CAPITOLUL 1",
                section="1.2 B",
                chunk_id="c2",
                text="fragment doi",
                is_list=False,
            ),
        ]

        with patch("rag.chunking.load_documents.parse_pdf_to_structured_chunks", return_value=base_chunks):
            with patch(
                "rag.chunking.load_documents.chunk_structured_chunks",
                side_effect=lambda chunks, **_: chunks,
            ):
                semantic_chunks = load_pdf_chunks(
                    "demo.pdf",
                    chunking_strategy="semantic",
                    semantic_chunk_max_chars=100,
                    semantic_use_llamaindex=False,
                )

        self.assertEqual(len(semantic_chunks), 1)
        self.assertIn("fragment unu", semantic_chunks[0].text)
        self.assertIn("fragment doi", semantic_chunks[0].text)

    def test_parse_pdf_handles_roman_and_numbered_headings(self) -> None:
        pages = [
            "\n".join(
                [
                    "Cavitatea bucala",
                    "I. Anatomie",
                    "Este formata din mucoasa bucala si glande salivare.",
                    "1. Limba",
                    "Limba formeaza podeaua cavitatii bucale.",
                    "• tulburari de deglutitie",
                    "✦ durere la masticatie",
                ]
            )
        ]
        with patch("rag.chunking.load_documents.extract_pdf_pages", return_value=pages):
            chunks = parse_pdf_to_structured_chunks("orl.pdf")

        self.assertGreaterEqual(len(chunks), 3)
        self.assertTrue(any(chunk.section == "I. Anatomie" for chunk in chunks))
        self.assertTrue(any(chunk.section == "1. Limba" for chunk in chunks))
        self.assertTrue(any(chunk.is_list for chunk in chunks))
        self.assertTrue(any("tulburari de deglutitie" in chunk.text for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
