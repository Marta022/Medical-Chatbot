from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from knowledge.entities.extractor import (
    extract_entities_from_chunk,
    extract_entities_from_chunks,
    load_disease_terms,
)
from models.contracts import PdfStructuredChunk


class TestEntities(unittest.TestCase):
    def test_load_disease_terms_reads_dataset_json(self) -> None:
        payload = [
            {
                "name": "Cat",
                "diseases": [{"name": "Infarct miocardic"}],
            }
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "diseases.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            terms = load_disease_terms(str(path))
        self.assertIn("infarct miocardic", terms)

    def test_extract_entities_from_chunk_uses_alias_and_symptoms(self) -> None:
        chunk = PdfStructuredChunk(
            source_file="doc.pdf",
            page=10,
            chapter="CAPITOLUL 1",
            section="1.1",
            chunk_id="chunk-1",
            text="Pacient cu MI, durere toracica si dispnee. Aspirina recomandata.",
            is_list=False,
        )
        entities = extract_entities_from_chunk(
            chunk,
            disease_terms={"infarct miocardic"},
            min_confidence=0.7,
        )
        canonical = {entity.canonical_form for entity in entities}
        self.assertIn("myocardial infarction", canonical)
        self.assertIn("durere toracica", canonical)
        self.assertIn("dispnee", canonical)
        self.assertIn("aspirina", canonical)
        self.assertTrue(all(entity.source_file == "doc.pdf" for entity in entities))
        self.assertTrue(all(entity.page == 10 for entity in entities))

    def test_extract_entities_from_chunks_applies_threshold(self) -> None:
        chunk = PdfStructuredChunk(
            source_file="doc.pdf",
            page=1,
            chapter="CAPITOLUL 1",
            section="1.1",
            chunk_id="chunk-2",
            text="Pacient cu tuse si febra.",
            is_list=False,
        )
        payload = [
            {"name": "Cat", "diseases": [{"name": "gripa"}]},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "diseases.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            high_threshold = extract_entities_from_chunks(
                [chunk],
                dataset_json_path=str(path),
                min_confidence=0.95,
            )
            low_threshold = extract_entities_from_chunks(
                [chunk],
                dataset_json_path=str(path),
                min_confidence=0.7,
            )

        self.assertEqual(high_threshold, [])
        self.assertGreaterEqual(len(low_threshold), 2)


if __name__ == "__main__":
    unittest.main()
