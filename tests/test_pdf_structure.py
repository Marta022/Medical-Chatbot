from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys

from models.contracts import PdfStructuredChunk
from rag.chunking.load_documents import (
    concatenate_page_markdown_files,
    _repair_common_mojibake_ro,
    _postprocess_markdown_cleanup,
    _split_text_for_llm_cleanup,
    _strip_markdown_code_fences,
    _build_lines_from_positioned_fragments,
    _group_structured_chunks_for_semantic,
    _merge_page_lines,
    _chunk_id_for,
    _decode_pdf_literal,
    extract_pdf_pages,
    extract_pdf_to_markdown,
    iter_pdf_pages_with_pymupdf,
    load_pdf_chunks,
    normalize_page_text_for_markdown_llm,
    parse_pdf_to_structured_chunks,
    profile_pdf_structure,
    write_page_markdown,
)


class TestPdfStructure(unittest.TestCase):
    def test_iter_pdf_pages_with_pymupdf_defaults_to_page_6(self) -> None:
        class _FakePage:
            def __init__(self, text: str) -> None:
                self._text = text

            def get_text(self, _mode: str) -> str:
                return self._text

        class _FakeDocument:
            def __init__(self, pages: list[str]) -> None:
                self._pages = pages
                self.page_count = len(pages)

            def load_page(self, index: int) -> _FakePage:
                return _FakePage(self._pages[index])

            def close(self) -> None:
                return None

        class _FakeFitz:
            @staticmethod
            def open(_path: str) -> _FakeDocument:
                return _FakeDocument(
                    [
                        "p1",
                        "p2",
                        "p3",
                        "p4",
                        "p5",
                        "p6 text",
                        "p7 text",
                    ]
                )

        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "demo.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            with patch.dict(sys.modules, {"fitz": _FakeFitz}):
                pages = list(iter_pdf_pages_with_pymupdf(str(pdf_path)))

        self.assertEqual(pages, [(6, "p6 text"), (7, "p7 text")])

    def test_iter_pdf_pages_with_pymupdf_respects_start_and_end(self) -> None:
        class _FakePage:
            def __init__(self, text: str) -> None:
                self._text = text

            def get_text(self, _mode: str) -> str:
                return self._text

        class _FakeDocument:
            def __init__(self, pages: list[str]) -> None:
                self._pages = pages
                self.page_count = len(pages)

            def load_page(self, index: int) -> _FakePage:
                return _FakePage(self._pages[index])

            def close(self) -> None:
                return None

        class _FakeFitz:
            @staticmethod
            def open(_path: str) -> _FakeDocument:
                return _FakeDocument(["a", "b", "c", "d", "e"])

        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "demo.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            with patch.dict(sys.modules, {"fitz": _FakeFitz}):
                pages = list(iter_pdf_pages_with_pymupdf(str(pdf_path), start_page=2, end_page=4))

        self.assertEqual(pages, [(2, "b"), (3, "c"), (4, "d")])

    def test_iter_pdf_pages_with_pymupdf_validates_page_range(self) -> None:
        with self.assertRaises(ValueError):
            list(iter_pdf_pages_with_pymupdf("missing.pdf", start_page=0))

        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "demo.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            with self.assertRaises(ValueError):
                list(iter_pdf_pages_with_pymupdf(str(pdf_path), start_page=6, end_page=5))

    def test_normalize_page_text_for_markdown_llm_repairs_line_wraps(self) -> None:
        text = "\n".join(
            [
                "Pacientul prezinta semne de insuficienta",
                "cardiaca cronica in stadiu avansat.",
                "",
                "Cu evolutie progresiva.",
            ]
        )
        normalized = normalize_page_text_for_markdown_llm(text)
        self.assertIn("insuficienta cardiaca cronica", normalized)
        self.assertIn("\n\n", normalized)

    def test_normalize_page_text_for_markdown_llm_preserves_headings_and_lists(self) -> None:
        text = "\n".join(
            [
                "CAPITOLUL 3 Cardiologie",
                "Introducere scurta in diagnostic",
                "clinic al afectiunilor cardiovasculare.",
                "",
                "1. Simptome",
                "2. Semne",
                "- dispnee",
                "- durere toracica",
            ]
        )
        normalized = normalize_page_text_for_markdown_llm(text)
        lines = normalized.splitlines()
        self.assertIn("CAPITOLUL 3 Cardiologie", lines)
        self.assertIn("1. Simptome", lines)
        self.assertIn("- dispnee", lines)
        self.assertTrue(
            any("Introducere scurta in diagnostic clinic" in line for line in lines),
        )

    def test_normalize_page_text_for_markdown_llm_repairs_hyphenated_breaks(self) -> None:
        normalized = normalize_page_text_for_markdown_llm("emboli-\nile sistemice")
        self.assertEqual(normalized, "emboliile sistemice")

    def test_write_page_markdown_uses_required_filename(self) -> None:
        with TemporaryDirectory() as temp_dir:
            path = write_page_markdown(
                output_dir=temp_dir,
                page_number=6,
                markdown_text="# Titlu\nContinut",
            )
            self.assertTrue(path.exists())
            self.assertEqual(path.name, "page_6.md")
            self.assertIn("# Titlu", path.read_text(encoding="utf-8"))

    def test_concatenate_page_markdown_files_orders_by_page_number(self) -> None:
        with TemporaryDirectory() as temp_dir:
            write_page_markdown(output_dir=temp_dir, page_number=10, markdown_text="P10")
            write_page_markdown(output_dir=temp_dir, page_number=6, markdown_text="P6")
            write_page_markdown(output_dir=temp_dir, page_number=7, markdown_text="P7")

            merged_path = concatenate_page_markdown_files(output_dir=temp_dir)
            merged = merged_path.read_text(encoding="utf-8")

        self.assertEqual(merged_path.name, "document.md")
        self.assertLess(merged.find("P6"), merged.find("P7"))
        self.assertLess(merged.find("P7"), merged.find("P10"))
        self.assertIn("\n\n---\n\n", merged)

    def test_concatenate_page_markdown_files_requires_existing_pages(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                concatenate_page_markdown_files(output_dir=temp_dir)

    def test_extract_pdf_to_markdown_writes_pages_and_document(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with patch(
                "rag.chunking.load_documents.iter_pdf_pages_with_pymupdf",
                return_value=[(6, "CAPITOLUL 1\nText"), (7, "1. Simptom\n2. Semn")],
            ):
                with patch("agent.reasoning.llm_router.llm_cleanup_pdf_page") as cleanup_mock:
                    cleanup_mock.side_effect = [
                        type("R", (), {"content": "# P6\nText"}),
                        type("R", (), {"content": "# P7\nLista"}),
                    ]
                    result = extract_pdf_to_markdown(
                        pdf_path="data/dataset/DORIN-CURS_SEM2_searchable.pdf",
                        output_dir=temp_dir,
                        start_page=6,
                        provider="openai",
                    )

            self.assertEqual(result["pages_processed"], 2)
            self.assertEqual(result["page_numbers"], [6, 7])
            self.assertEqual(result["failed_pages"], [])
            self.assertTrue((Path(temp_dir) / "page_6.md").exists())
            self.assertTrue((Path(temp_dir) / "page_7.md").exists())
            self.assertTrue((Path(temp_dir) / "document.md").exists())

    def test_extract_pdf_to_markdown_respects_batch_limit(self) -> None:
        with TemporaryDirectory() as temp_dir:
            with patch(
                "rag.chunking.load_documents.iter_pdf_pages_with_pymupdf",
                return_value=[(6, "A"), (7, "B"), (8, "C")],
            ):
                with patch(
                    "agent.reasoning.llm_router.llm_cleanup_pdf_page",
                    return_value=type("R", (), {"content": "ok"}),
                ):
                    result = extract_pdf_to_markdown(
                        pdf_path="data/dataset/DORIN-CURS_SEM2_searchable.pdf",
                        output_dir=temp_dir,
                        start_page=6,
                        max_pages_per_run=2,
                        provider="openai",
                    )

        self.assertEqual(result["pages_processed"], 2)
        self.assertEqual(result["page_numbers"], [6, 7])

    def test_extract_pdf_to_markdown_handles_large_page_ranges_with_batching(self) -> None:
        synthetic_pages = [(index, f"Page {index} content") for index in range(6, 356)]
        with TemporaryDirectory() as temp_dir:
            with patch(
                "rag.chunking.load_documents.iter_pdf_pages_with_pymupdf",
                return_value=synthetic_pages,
            ):
                with patch(
                    "agent.reasoning.llm_router.llm_cleanup_pdf_page",
                    return_value=type("R", (), {"content": "ok"}),
                ):
                    result = extract_pdf_to_markdown(
                        pdf_path="data/dataset/DORIN-CURS_SEM2_searchable.pdf",
                        output_dir=temp_dir,
                        start_page=6,
                        max_pages_per_run=25,
                        provider="openai",
                    )

        self.assertEqual(result["pages_processed"], 25)
        self.assertEqual(result["page_numbers"][0], 6)
        self.assertEqual(result["page_numbers"][-1], 30)

    def test_repair_common_mojibake_ro_fixes_diacritics(self) -> None:
        raw = "tensiune arterialÄƒ, ÅŸoc, infecÅ£ie, Ã®nceput"
        repaired = _repair_common_mojibake_ro(raw)
        self.assertIn("arterială", repaired)
        self.assertIn("șoc", repaired)
        self.assertIn("infecție", repaired)
        self.assertIn("început", repaired)

    def test_split_text_for_llm_cleanup_breaks_large_input(self) -> None:
        text = ("Paragraf lung. " * 400) + "\n\n" + ("Al doilea paragraf. " * 300)
        chunks = _split_text_for_llm_cleanup(text, max_chars=1200)
        self.assertGreater(len(chunks), 1)
        self.assertTrue(all(len(chunk) <= 1200 for chunk in chunks))

    def test_strip_markdown_code_fences_removes_wrappers(self) -> None:
        fenced = "```markdown\n# Titlu\nText\n```"
        self.assertEqual(_strip_markdown_code_fences(fenced), "# Titlu\nText")

    def test_postprocess_markdown_cleanup_removes_noisy_tokens(self) -> None:
        raw = "Temperatura OQfI!J~lÄƒ este 37,7Â°C \"7 normal.\nfe.JJL{LLQ[Â§,S\\lgciÈ™~"
        cleaned = _postprocess_markdown_cleanup(raw)
        self.assertIn("Temperatura", cleaned)
        self.assertIn("37,7", cleaned)
        self.assertNotIn("OQfI!J~lÄƒ", cleaned)
        self.assertNotIn("fe.JJL{LLQ[Â§,S\\lgciÈ™~", cleaned)

    def test_extract_pdf_pages_raises_when_pymupdf_extracts_no_pages(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "demo.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            with patch(
                "rag.chunking.load_documents._extract_pages_with_pymupdf",
                return_value={},
            ):
                with self.assertRaisesRegex(ValueError, "PyMuPDF"):
                    extract_pdf_pages(str(pdf_path))

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
            with patch(
                "rag.chunking.load_documents._semantic_chunk_structured_chunks_with_llamaindex",
                return_value=[
                    PdfStructuredChunk(
                        source_file="DORIN-CURS_SEM2_searchable.pdf",
                        page=1,
                        chapter="CAPITOLUL 1",
                        section="1.1 Sectiune",
                        chunk_id="semantic-1",
                        text="Text simplu de test.",
                        is_list=False,
                    )
                ],
            ):
                semantic_chunks = load_pdf_chunks(
                    "DORIN-CURS_SEM2_searchable.pdf",
                    chunking_strategy="semantic",
                    semantic_chunk_max_chars=50,
                    semantic_use_llamaindex=True,
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

    def test_load_pdf_chunks_semantic_requires_llamaindex_toggle(self) -> None:
        pages = ["CAPITOLUL 1\n1.1 Sectiune\nText."]
        with patch("rag.chunking.load_documents.extract_pdf_pages", return_value=pages):
            with self.assertRaises(RuntimeError):
                load_pdf_chunks(
                    "demo.pdf",
                    chunking_strategy="semantic",
                    semantic_use_llamaindex=False,
                )

    def test_load_pdf_chunks_semantic_uses_llamaindex_rechunker(self) -> None:
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

        semantic_out = [
            PdfStructuredChunk(
                source_file="demo.pdf",
                page=1,
                chapter="CAPITOLUL 1",
                section="1.1 A",
                chunk_id="s1",
                text="fragment semantic",
                is_list=False,
            )
        ]
        with patch("rag.chunking.load_documents.parse_pdf_to_structured_chunks", return_value=base_chunks):
            with patch(
                "rag.chunking.load_documents._semantic_chunk_structured_chunks_with_llamaindex",
                return_value=semantic_out,
            ) as semantic_mock:
                semantic_chunks = load_pdf_chunks(
                    "demo.pdf",
                    chunking_strategy="semantic",
                    semantic_chunk_max_chars=100,
                    semantic_use_llamaindex=True,
                )

        semantic_mock.assert_called_once_with(base_chunks)
        self.assertEqual(semantic_chunks, semantic_out)

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
