from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from rag.chunking.load_documents import discover_pdf_paths, load_medical_items


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
            validation = dataset_dir / "DORIN_GENERALA_CARDIOVASCULARA-RESPIRATORIE-DISESTIVA.CV01.pdf"
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


if __name__ == "__main__":
    unittest.main()
