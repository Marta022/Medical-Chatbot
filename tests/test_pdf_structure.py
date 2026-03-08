from __future__ import annotations

import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from models.contracts import (
    PdfStructuredChunk,
    TocAgentEntry,
    TocPageValidationConfig,
    TocValidatedEntry,
    TocValidationResult,
)
from rag.chunking.load_documents import (
    _clean_section_page_texts,
    _build_lines_from_positioned_fragments,
    _build_toc_line_records_from_blocks,
    _build_toc_lines_from_blocks,
    _match_printed_page_marker,
    _detect_two_column_layout,
    _OcrTextBlock,
    _group_structured_chunks_for_semantic,
    _merge_page_lines,
    _chunk_id_for,
    _decode_pdf_literal,
    extract_pdf_pages,
    aggregate_toc_section_contents,
    extract_toc_page_lines,
    extract_toc_page_records,
    extract_section_text_range,
    export_toc_sections_to_json,
    export_toc_sections_with_validation_to_json,
    interpret_toc_entries_with_agent,
    load_pdf_chunks,
    parse_toc_entries,
    preprocess_toc_records_for_agent,
    resolve_toc_page_ranges,
    parse_pdf_to_structured_chunks,
    profile_pdf_structure,
    validate_toc_start_pages,
    aggregate_validated_toc_section_contents,
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

    def test_extract_toc_page_lines_prefers_native_when_quality_is_good(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "toc.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            native_blocks = [
                _OcrTextBlock(x=40, y=100, text="Capitol 1 ........ 7"),
                _OcrTextBlock(x=40, y=110, text="Capitol 2 ........ 12"),
                _OcrTextBlock(x=300, y=100, text="Capitol 3 ........ 20"),
                _OcrTextBlock(x=300, y=110, text="Capitol 4 ........ 28"),
                _OcrTextBlock(x=45, y=120, text="Capitol 5 ........ 35"),
                _OcrTextBlock(x=305, y=120, text="Capitol 6 ........ 41"),
                _OcrTextBlock(x=50, y=130, text="Capitol 7 ........ 49"),
                _OcrTextBlock(x=310, y=130, text="Capitol 8 ........ 57"),
            ]
            with patch(
                "rag.chunking.load_documents._extract_toc_blocks_with_pymupdf",
                return_value=native_blocks,
            ) as native_mock:
                with patch(
                    "rag.chunking.load_documents._extract_toc_blocks_with_ocr",
                    return_value=[],
                ) as ocr_mock:
                    lines = extract_toc_page_lines(
                        str(pdf_path),
                        toc_page_index=1,
                        expected_columns=2,
                        min_native_text_chars=30,
                    )
        self.assertTrue(lines[0].startswith("Capitol 1"))
        self.assertTrue(lines[3].startswith("Capitol 7"))
        self.assertTrue(lines[-1].startswith("Capitol 8"))
        native_mock.assert_called_once()
        ocr_mock.assert_not_called()

    def test_extract_toc_page_lines_falls_back_to_ocr_when_native_is_poor(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "toc.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            poor_native = [_OcrTextBlock(x=40, y=100, text="x")]
            ocr_blocks = [
                _OcrTextBlock(x=30, y=100, text="L1"),
                _OcrTextBlock(x=30, y=110, text="L2"),
                _OcrTextBlock(x=300, y=100, text="R1"),
                _OcrTextBlock(x=300, y=110, text="R2"),
                _OcrTextBlock(x=35, y=120, text="L3"),
                _OcrTextBlock(x=305, y=120, text="R3"),
                _OcrTextBlock(x=40, y=130, text="L4"),
                _OcrTextBlock(x=310, y=130, text="R4"),
            ]
            with patch(
                "rag.chunking.load_documents._extract_toc_blocks_with_pymupdf",
                return_value=poor_native,
            ):
                with patch(
                    "rag.chunking.load_documents._extract_toc_blocks_with_ocr",
                    return_value=ocr_blocks,
                ) as ocr_mock:
                    lines = extract_toc_page_lines(
                        str(pdf_path),
                        toc_page_index=1,
                        expected_columns=2,
                        min_native_text_chars=50,
                    )
        self.assertEqual(lines[:4], ["L1", "L2", "L3", "L4"])
        self.assertEqual(lines[4:], ["R1", "R2", "R3", "R4"])
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

    def test_detect_two_column_layout_from_blocks(self) -> None:
        blocks = [
            _OcrTextBlock(x=40, y=100, text="A"),
            _OcrTextBlock(x=45, y=120, text="B"),
            _OcrTextBlock(x=50, y=140, text="C"),
            _OcrTextBlock(x=55, y=160, text="D"),
            _OcrTextBlock(x=300, y=100, text="E"),
            _OcrTextBlock(x=305, y=120, text="F"),
            _OcrTextBlock(x=310, y=140, text="G"),
            _OcrTextBlock(x=315, y=160, text="H"),
        ]
        layout = _detect_two_column_layout(blocks)
        self.assertEqual(layout.column_count, 2)
        self.assertIsNotNone(layout.split_x)

    def test_build_toc_lines_from_blocks_enforces_left_then_right(self) -> None:
        blocks = [
            _OcrTextBlock(x=40, y=100, text="L1"),
            _OcrTextBlock(x=40, y=110, text="L2"),
            _OcrTextBlock(x=300, y=100, text="R1"),
            _OcrTextBlock(x=300, y=110, text="R2"),
            _OcrTextBlock(x=45, y=120, text="L3"),
            _OcrTextBlock(x=305, y=120, text="R3"),
            _OcrTextBlock(x=50, y=130, text="L4"),
            _OcrTextBlock(x=310, y=130, text="R4"),
        ]
        lines = _build_toc_lines_from_blocks(blocks, expected_columns=2)
        self.assertEqual(lines[:4], ["L1", "L2", "L3", "L4"])
        self.assertEqual(lines[4:], ["R1", "R2", "R3", "R4"])

    def test_build_toc_line_records_preserves_x_positions(self) -> None:
        blocks = [
            _OcrTextBlock(x=40, y=100, text="Capitol 1 ..... 7"),
            _OcrTextBlock(x=68, y=120, text="1.1 Sectiune ..... 8"),
            _OcrTextBlock(x=40, y=140, text="Capitol 2 ..... 12"),
            _OcrTextBlock(x=68, y=160, text="2.1 Sectiune ..... 13"),
            _OcrTextBlock(x=300, y=100, text="Capitol 3 ..... 18"),
            _OcrTextBlock(x=325, y=120, text="3.1 Sectiune ..... 19"),
            _OcrTextBlock(x=300, y=140, text="Capitol 4 ..... 24"),
            _OcrTextBlock(x=325, y=160, text="4.1 Sectiune ..... 25"),
        ]
        records = _build_toc_line_records_from_blocks(blocks, expected_columns=2)
        self.assertEqual(records[0].text, "Capitol 1 ..... 7")
        self.assertEqual(records[1].text, "1.1 Sectiune ..... 8")
        self.assertLess(records[0].x, records[1].x)

    def test_extract_toc_page_records_returns_x_text_pairs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "toc.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            native_blocks = [
                _OcrTextBlock(x=40, y=100, text="Capitol 1 ..... 7"),
                _OcrTextBlock(x=70, y=120, text="1.1 Sectiune ..... 8"),
                _OcrTextBlock(x=300, y=100, text="Capitol 2 ..... 12"),
                _OcrTextBlock(x=330, y=120, text="2.1 Sectiune ..... 13"),
                _OcrTextBlock(x=45, y=140, text="Capitol 3 ..... 18"),
                _OcrTextBlock(x=75, y=160, text="3.1 Sectiune ..... 19"),
                _OcrTextBlock(x=305, y=140, text="Capitol 4 ..... 24"),
                _OcrTextBlock(x=335, y=160, text="4.1 Sectiune ..... 25"),
            ]
            with patch(
                "rag.chunking.load_documents._extract_toc_blocks_with_pymupdf",
                return_value=native_blocks,
            ):
                records = extract_toc_page_records(
                    str(pdf_path),
                    toc_page_index=1,
                    expected_columns=2,
                    min_native_text_chars=20,
                )
        self.assertTrue(records)
        self.assertIsInstance(records[0][0], (float, int))
        self.assertIsInstance(records[0][1], str)

    def test_parse_toc_entries_uses_indentation_for_subchapters(self) -> None:
        toc_records = [
            (40.0, "Contents ..... 1"),
            (40.0, "Capitol 1 Introducere ..... 7"),
            (68.0, "1.1 Anatomie ..... 8"),
            (68.0, "1.2 Fiziologie ..... 10"),
            (40.0, "Capitol 2 Patologie ..... 12"),
            (69.0, "2.1 Sindromul Cushing ..... 13"),
        ]
        entries = parse_toc_entries(toc_records, ignored_terms=("contents",))
        self.assertEqual(len(entries), 5)
        self.assertEqual(entries[0].chapter, "Capitol 1 Introducere")
        self.assertIsNone(entries[0].subchapter)
        self.assertEqual(entries[1].chapter, "Capitol 1 Introducere")
        self.assertEqual(entries[1].subchapter, "1.1 Anatomie")
        self.assertEqual(entries[2].subchapter, "1.2 Fiziologie")
        self.assertEqual(entries[3].chapter, "Capitol 2 Patologie")
        self.assertEqual(entries[4].subchapter, "2.1 Sindromul Cushing")

    def test_preprocess_toc_records_for_agent_merges_wrapped_lines(self) -> None:
        toc_records = [
            (40.0, "Capitol 1 Introducere"),
            (40.0, "..... 7"),
            (68.0, "1.1 Anatomie ..... 8"),
        ]
        normalized = preprocess_toc_records_for_agent(toc_records)
        self.assertEqual(len(normalized), 2)
        self.assertEqual(normalized[0][1], "Capitol 1 Introducere ..... 7")

    def test_interpret_toc_entries_with_agent_uses_fallback_parser(self) -> None:
        toc_records = [
            (40.0, "Capitol 1 Introducere ..... 7"),
            (68.0, "1.1 Anatomie ..... 8"),
        ]
        entries = interpret_toc_entries_with_agent(toc_records)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0].printed_start_page, 7)
        self.assertEqual(entries[1].subchapter, "1.1 Anatomie")

    def test_interpret_toc_entries_with_agent_supports_injected_interpreter(self) -> None:
        def _fake_agent(_records: list[tuple[float, str]]) -> list[TocAgentEntry]:
            return [
                TocAgentEntry(
                    chapter="Capitol Agent",
                    subchapter=None,
                    printed_start_page=11,
                    original_toc_text="Capitol Agent .... 11",
                )
            ]

        entries = interpret_toc_entries_with_agent([], agent_interpreter=_fake_agent)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].chapter, "Capitol Agent")

    def test_validate_toc_start_pages_applies_offset_mapping_default(self) -> None:
        entries = [
            TocAgentEntry(
                chapter="Capitol 1",
                subchapter=None,
                printed_start_page=7,
                original_toc_text="Capitol 1 .... 7",
            )
        ]
        result = validate_toc_start_pages(
            entries,
            config=TocPageValidationConfig(expected_page_offset=2, search_window=1),
        )
        self.assertEqual(result.entries[0].validated_start_page, 9)
        self.assertEqual(result.entries[0].page_validation_status, "OFFSET_MAPPED")

    def test_validate_toc_start_pages_uses_page_markers_and_title_hints(self) -> None:
        entries = [
            TocAgentEntry(
                chapter="Capitol 1",
                subchapter="1.1 Anatomie",
                printed_start_page=7,
                original_toc_text="1.1 Anatomie .... 7",
            )
        ]

        def _provider(page_number: int) -> str:
            if page_number == 9:
                return "Pagina 7\n1.1 Anatomie si fiziologie"
            return "Pagina 6\nAlt continut"

        result = validate_toc_start_pages(
            entries,
            config=TocPageValidationConfig(expected_page_offset=1, search_window=2),
            page_text_provider=_provider,
        )
        self.assertEqual(result.entries[0].validated_start_page, 9)
        self.assertEqual(result.entries[0].page_validation_status, "MATCHED_HEADER_AND_TITLE")
        self.assertEqual(result.entries[0].matched_page_marker, "Pagina 7")

    def test_match_printed_page_marker_detects_marker_line(self) -> None:
        marker = _match_printed_page_marker("Titlu\nPagina 12\nText", 12)
        self.assertEqual(marker, "Pagina 12")

    def test_aggregate_validated_toc_section_contents_uses_validated_boundaries(self) -> None:
        validated = [
            TocValidatedEntry(
                chapter="Capitol 1",
                subchapter=None,
                printed_start_page=7,
                validated_start_page=9,
                original_toc_text="Capitol 1 ... 7",
                page_validation_status="MATCHED_HEADER",
                page_validation_method="window_search",
            ),
            TocValidatedEntry(
                chapter="Capitol 2",
                subchapter=None,
                printed_start_page=10,
                validated_start_page=12,
                original_toc_text="Capitol 2 ... 10",
                page_validation_status="MATCHED_HEADER",
                page_validation_method="window_search",
            ),
        ]
        with patch("rag.chunking.load_documents._pdf_page_count", return_value=20):
            with patch(
                "rag.chunking.load_documents.extract_section_text_range",
                side_effect=["Text sectiunea 1", "Text sectiunea 2"],
            ) as extract_mock:
                sections = aggregate_validated_toc_section_contents("demo.pdf", validated)
        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].validated_start_page, 9)
        self.assertEqual(sections[0].validated_end_page, 11)
        self.assertEqual(sections[1].validated_start_page, 12)
        self.assertEqual(sections[1].validated_end_page, 20)
        self.assertEqual(extract_mock.call_count, 2)

    def test_export_toc_sections_with_validation_to_json_writes_dual_outputs(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "doc.pdf"
            out_sections = Path(temp_dir) / "sections.json"
            out_toc = Path(temp_dir) / "toc_entries.json"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")

            with patch(
                "rag.chunking.load_documents.extract_toc_page_records",
                return_value=[(40.0, "Capitol 1 ..... 7")],
            ):
                with patch(
                    "rag.chunking.load_documents.validate_toc_start_pages",
                    return_value=TocValidationResult(
                        entries=[
                            TocValidatedEntry(
                                chapter="Capitol 1",
                                subchapter=None,
                                printed_start_page=7,
                                validated_start_page=9,
                                original_toc_text="Capitol 1 ..... 7",
                                page_validation_status="OFFSET_MAPPED",
                                page_validation_method="offset_only",
                            )
                        ],
                        config=TocPageValidationConfig(expected_page_offset=2, search_window=2),
                    ),
                ):
                    with patch(
                        "rag.chunking.load_documents.aggregate_validated_toc_section_contents",
                        return_value=[],
                    ):
                        toc_entries, sections = export_toc_sections_with_validation_to_json(
                            str(pdf_path),
                            output_json_path=str(out_sections),
                            toc_entries_json_path=str(out_toc),
                        )

            self.assertEqual(len(toc_entries), 1)
            self.assertEqual(len(sections), 0)
            toc_payload = json.loads(out_toc.read_text(encoding="utf-8"))
            sections_payload = json.loads(out_sections.read_text(encoding="utf-8"))
            self.assertEqual(len(toc_payload), 1)
            self.assertEqual(toc_payload[0]["chapter"], "Capitol 1")
            self.assertEqual(sections_payload, [])

    def test_resolve_toc_page_ranges_applies_offset_and_infers_end(self) -> None:
        entries = parse_toc_entries(
            [
                (40.0, "Capitol 1 Introducere ..... 7"),
                (68.0, "1.1 Anatomie ..... 8"),
                (40.0, "Capitol 2 Patologie ..... 12"),
            ]
        )
        resolved = resolve_toc_page_ranges(entries, page_offset=2)
        self.assertEqual(resolved[0].start_page, 9)
        self.assertEqual(resolved[0].end_page, 9)
        self.assertEqual(resolved[1].start_page, 10)
        self.assertEqual(resolved[1].end_page, 13)
        self.assertEqual(resolved[2].start_page, 14)
        self.assertEqual(resolved[2].end_page, 14)

    def test_resolve_toc_page_ranges_clamps_to_max_pdf_page(self) -> None:
        entries = parse_toc_entries(
            [
                (40.0, "Capitol 1 ..... 7"),
                (40.0, "Capitol 2 ..... 12"),
            ]
        )
        resolved = resolve_toc_page_ranges(entries, page_offset=0, max_pdf_page=10)
        self.assertEqual(resolved[0].start_page, 7)
        self.assertEqual(resolved[0].end_page, 10)
        self.assertEqual(resolved[1].start_page, 10)
        self.assertEqual(resolved[1].end_page, 10)

    def test_extract_section_text_range_prefers_native_when_sufficient(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "section.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            native_page_1 = [
                _OcrTextBlock(x=40, y=100, text="L1"),
                _OcrTextBlock(x=40, y=120, text="L2"),
                _OcrTextBlock(x=300, y=100, text="R1"),
                _OcrTextBlock(x=300, y=120, text="R2"),
                _OcrTextBlock(x=45, y=140, text="L3"),
                _OcrTextBlock(x=45, y=160, text="L4"),
                _OcrTextBlock(x=305, y=140, text="R3"),
                _OcrTextBlock(x=305, y=160, text="R4"),
            ]
            native_page_2 = [
                _OcrTextBlock(x=40, y=100, text="L5"),
                _OcrTextBlock(x=40, y=120, text="L6"),
                _OcrTextBlock(x=300, y=100, text="R5"),
                _OcrTextBlock(x=300, y=120, text="R6"),
                _OcrTextBlock(x=45, y=140, text="L7"),
                _OcrTextBlock(x=45, y=160, text="L8"),
                _OcrTextBlock(x=305, y=140, text="R7"),
                _OcrTextBlock(x=305, y=160, text="R8"),
            ]
            with patch(
                "rag.chunking.load_documents._extract_page_blocks_with_pymupdf",
                side_effect=[native_page_1, native_page_2],
            ):
                with patch(
                    "rag.chunking.load_documents._extract_page_blocks_with_pp_structure",
                    return_value=[],
                ) as pp_mock:
                    text = extract_section_text_range(
                        str(pdf_path),
                        start_page=1,
                        end_page=2,
                        expected_columns=2,
                        min_native_text_chars=2,
                    )
        self.assertIn("L1", text)
        self.assertIn("R8", text)
        pp_mock.assert_not_called()

    def test_extract_section_text_range_falls_back_to_pp_structure(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "section.pdf"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            poor_native = [_OcrTextBlock(x=40, y=100, text="x")]
            pp_blocks = [
                _OcrTextBlock(x=40, y=100, text="Capitol 1"),
                _OcrTextBlock(x=70, y=120, text="1.1 Anatomie"),
                _OcrTextBlock(x=40, y=140, text="Text extins pentru fallback"),
                _OcrTextBlock(x=300, y=100, text="Continuare"),
                _OcrTextBlock(x=300, y=120, text="detalii"),
                _OcrTextBlock(x=300, y=140, text="suplimentare"),
                _OcrTextBlock(x=40, y=160, text="linie"),
                _OcrTextBlock(x=300, y=160, text="finala"),
            ]
            with patch(
                "rag.chunking.load_documents._extract_page_blocks_with_pymupdf",
                return_value=poor_native,
            ):
                with patch(
                    "rag.chunking.load_documents._extract_page_blocks_with_pp_structure",
                    return_value=pp_blocks,
                ) as pp_mock:
                    text = extract_section_text_range(
                        str(pdf_path),
                        start_page=1,
                        end_page=1,
                        expected_columns=2,
                        min_native_text_chars=50,
                        use_pp_structure_fallback=True,
                    )
        self.assertIn("Capitol 1", text)
        self.assertIn("finala", text)
        pp_mock.assert_called_once()

    def test_clean_section_page_texts_removes_repeated_headers_footers_and_page_numbers(self) -> None:
        page_texts = [
            "\n".join(
                [
                    "CURS MEDICAL - SEMESTRUL 2",
                    "Continut util pagina 1",
                    "1",
                    "Universitatea X",
                ]
            ),
            "\n".join(
                [
                    "CURS MEDICAL - SEMESTRUL 2",
                    "Continut util pagina 2",
                    "2",
                    "Universitatea X",
                ]
            ),
        ]
        cleaned = _clean_section_page_texts(page_texts)
        self.assertNotIn("CURS MEDICAL - SEMESTRUL 2", cleaned)
        self.assertNotIn("Universitatea X", cleaned)
        self.assertNotIn("\n1\n", f"\n{cleaned}\n")
        self.assertIn("Continut util pagina 1", cleaned)
        self.assertIn("Continut util pagina 2", cleaned)

    def test_aggregate_toc_section_contents_builds_section_payloads(self) -> None:
        toc_entries = parse_toc_entries(
            [
                (40.0, "Capitol 1 ..... 7"),
                (68.0, "1.1 Anatomie ..... 8"),
            ]
        )
        resolved = resolve_toc_page_ranges(toc_entries, page_offset=0)
        with patch(
            "rag.chunking.load_documents.extract_section_text_range",
            side_effect=["Text capitol", "Text subcapitol"],
        ):
            sections = aggregate_toc_section_contents(
                "demo.pdf",
                resolved,
                expected_columns=2,
                min_native_text_chars=20,
            )

        self.assertEqual(len(sections), 2)
        self.assertEqual(sections[0].chapter, "Capitol 1")
        self.assertIsNone(sections[0].subchapter)
        self.assertEqual(sections[1].subchapter, "1.1 Anatomie")
        self.assertIn("Text subcapitol", sections[1].text)

    def test_export_toc_sections_to_json_writes_payload(self) -> None:
        with TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "doc.pdf"
            out_path = Path(temp_dir) / "out.json"
            pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
            toc_records = [(40.0, "Capitol 1 ..... 7"), (68.0, "1.1 Anatomie ..... 8")]
            with patch(
                "rag.chunking.load_documents.extract_toc_page_records",
                return_value=toc_records,
            ):
                with patch(
                    "rag.chunking.load_documents._pdf_page_count",
                    return_value=20,
                ):
                    with patch(
                        "rag.chunking.load_documents.extract_section_text_range",
                        side_effect=["Text capitol", "Text subcapitol"],
                    ):
                        sections = export_toc_sections_to_json(
                            str(pdf_path),
                            output_json_path=str(out_path),
                            toc_page_index=1,
                            expected_columns=2,
                            page_offset=0,
                            min_native_text_chars=120,
                        )

            self.assertEqual(len(sections), 2)
            payload = json.loads(out_path.read_text(encoding="utf-8"))
            self.assertEqual(len(payload), 2)
            self.assertEqual(payload[0]["chapter"], "Capitol 1")
            self.assertEqual(payload[1]["subchapter"], "1.1 Anatomie")

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
    aggregate_toc_section_contents,
