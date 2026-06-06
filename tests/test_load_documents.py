from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from rag.chunking.load_documents import (
    _normalize_markdown_for_ingest,
    discover_markdown_paths,
    discover_pdf_paths,
    load_medical_items,
    parse_markdown_to_structured_chunks,
)


class TestLoadDocuments(unittest.TestCase):
    def test_load_medical_items_happy_path(self) -> None:
        data = [
            {
                "name": "Respirator",
                "diseases": [
                    {
                        "name": "Gripa",
                        "description": "Febra",
                        "symptoms": "Tuse",
                        "treatment": "Odihna",
                    }
                ],
            }
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "data.json"
            csv_path = Path(tmpdir) / "data.csv"
            json_path.write_text(json.dumps(data), encoding="utf-8")
            csv_path.write_text(
                "disease,symptom\nraceala,odihna\n",
                encoding="utf-8",
            )

            items = load_medical_items(str(json_path), str(csv_path))

        self.assertGreaterEqual(len(items), 2)

    def test_load_medical_items_reports_validation_errors(self) -> None:
        invalid_data = {"name": "bad"}
        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "data.json"
            csv_path = Path(tmpdir) / "data.csv"
            json_path.write_text(json.dumps(invalid_data), encoding="utf-8")
            csv_path.write_text("a,b\n", encoding="utf-8")

            with self.assertRaises(ValueError) as ctx:
                load_medical_items(str(json_path), str(csv_path))

        self.assertIn("JSON root must be a list", str(ctx.exception))

    def test_discover_pdf_paths_excludes_known_validation_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir = Path(tmpdir)
            primary = dataset_dir / "DORIN-CURS_SEM2_searchable.pdf"
            validation = (
                dataset_dir / "DORIN_GENERALA_CARDIOVASCULARA-RESPIRATORIE-DISESTIVA.CV01.pdf"
            )
            notes = dataset_dir / "notes.txt"

            primary.write_bytes(b"%PDF-1.4")
            validation.write_bytes(b"%PDF-1.4")
            notes.write_text("ignore", encoding="utf-8")

            discovered = discover_pdf_paths(
                str(dataset_dir),
                excluded_paths=[str(validation)],
            )

        self.assertEqual(len(discovered), 1)
        self.assertTrue(discovered[0].endswith("DORIN-CURS_SEM2_searchable.pdf"))

    def test_discover_markdown_paths_prefers_document_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset_dir = Path(tmpdir)
            (dataset_dir / "notes.md").write_text("# Notes", encoding="utf-8")
            preferred = dataset_dir / "document.md"
            preferred.write_text("# Main Document", encoding="utf-8")

            discovered = discover_markdown_paths(str(dataset_dir))

        self.assertEqual(discovered, [str(preferred)])

    def test_parse_markdown_to_structured_chunks_extracts_headings_and_lists(self) -> None:
        markdown = "\n".join(
            [
                "# Capitol 1",
                "## Sectiune 1.1",
                "Paragraf introductiv.",
                "",
                "- Primul punct",
                "- Al doilea punct",
            ]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "document.md"
            markdown_path.write_text(markdown, encoding="utf-8")

            chunks = parse_markdown_to_structured_chunks(str(markdown_path))

        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(all(chunk.source_file == "document.md" for chunk in chunks))
        self.assertTrue(all(chunk.chapter == "Capitol 1" for chunk in chunks))
        self.assertTrue(all(chunk.section == "Sectiune 1.1" for chunk in chunks))
        self.assertTrue(any(chunk.is_list for chunk in chunks))
        self.assertTrue(all(chunk.chunk_id for chunk in chunks))

    def test_normalize_markdown_for_ingest_repairs_mojibake_and_removes_noise(self) -> None:
        raw = "\n".join(
            [
                "```markdown",
                "# Semiologie generalÄƒ",
                "Temperatura corporalÄƒ.",
                "fe.JJL{LLQ[Â§,S\\lgciÈ™~",
                "```",
            ]
        )
        normalized = _normalize_markdown_for_ingest(raw)
        self.assertIn("# Semiologie generală", normalized)
        self.assertIn("Temperatura corporală.", normalized)
        self.assertNotIn("fe.JJL{LLQ[Â§,S\\lgciÈ™~", normalized)

    def test_parse_markdown_to_structured_chunks_applies_ingest_normalization(self) -> None:
        markdown = "\n".join(
            [
                "# Capitol 1",
                "## Sectiune 1.1",
                "Text cu diacritice: temperaturÄƒ crescutÄƒ.",
                "LLQ[Â§,S\\lgciÈ™~",
            ]
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            markdown_path = Path(tmpdir) / "document.md"
            markdown_path.write_text(markdown, encoding="utf-8")

            chunks = parse_markdown_to_structured_chunks(str(markdown_path))

        merged = " ".join(chunk.text for chunk in chunks)
        self.assertIn("temperatură", merged)
        self.assertNotIn("LLQ[Â§,S\\lgciÈ™~", merged)


if __name__ == "__main__":
    unittest.main()
