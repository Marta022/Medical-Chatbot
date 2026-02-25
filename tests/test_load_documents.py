from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from rag.chunking.load_documents import load_medical_items


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


if __name__ == "__main__":
    unittest.main()
