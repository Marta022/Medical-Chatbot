from __future__ import annotations

import unittest

from knowledge.graph.relations import extract_relations_from_chunk
from models.contracts import MedicalEntity, PdfStructuredChunk


class TestGraphRelations(unittest.TestCase):
    def test_extract_relations_from_chunk_emits_required_predicates(self) -> None:
        chunk = PdfStructuredChunk(
            source_file="doc.pdf",
            page=5,
            chapter="CAPITOLUL 2",
            section="2.1",
            chunk_id="chunk-rel-1",
            text=(
                "Pacientul cu infarct miocardic are durere toracica. "
                "Aspirina trateaza infarctul miocardic si boala determina dispnee."
            ),
        )
        entities = [
            MedicalEntity(
                entity_type="disease",
                mention_text="infarct miocardic",
                canonical_form="myocardial infarction",
                confidence=0.9,
                source_file="doc.pdf",
                page=5,
                chunk_id="chunk-rel-1",
            ),
            MedicalEntity(
                entity_type="symptom",
                mention_text="durere toracica",
                canonical_form="durere toracica",
                confidence=0.8,
                source_file="doc.pdf",
                page=5,
                chunk_id="chunk-rel-1",
            ),
            MedicalEntity(
                entity_type="symptom",
                mention_text="dispnee",
                canonical_form="dispnee",
                confidence=0.8,
                source_file="doc.pdf",
                page=5,
                chunk_id="chunk-rel-1",
            ),
            MedicalEntity(
                entity_type="drug",
                mention_text="aspirina",
                canonical_form="aspirina",
                confidence=0.82,
                source_file="doc.pdf",
                page=5,
                chunk_id="chunk-rel-1",
            ),
        ]

        relations = extract_relations_from_chunk(chunk, entities)
        predicates = {relation.predicate for relation in relations}

        self.assertIn("disease_has_symptom", predicates)
        self.assertIn("drug_treats_disease", predicates)
        self.assertIn("condition_causes_symptom", predicates)

    def test_extract_relations_from_chunk_detects_differential_diagnosis(self) -> None:
        chunk = PdfStructuredChunk(
            source_file="doc.pdf",
            page=8,
            chapter="CAPITOLUL 3",
            section="3.2",
            chunk_id="chunk-rel-2",
            text="Diagnosticul diferential: pneumonie versus bronhopneumopatie obstructiva cronica.",
        )
        entities = [
            MedicalEntity(
                entity_type="disease",
                mention_text="pneumonie",
                canonical_form="pneumonie",
                confidence=0.9,
                source_file="doc.pdf",
                page=8,
                chunk_id="chunk-rel-2",
            ),
            MedicalEntity(
                entity_type="disease",
                mention_text="bpoc",
                canonical_form="bronhopneumopatie obstructiva cronica",
                confidence=0.85,
                source_file="doc.pdf",
                page=8,
                chunk_id="chunk-rel-2",
            ),
        ]

        relations = extract_relations_from_chunk(chunk, entities, min_confidence=0.7)
        predicates = {relation.predicate for relation in relations}
        self.assertIn("disease_differs_from_disease", predicates)

    def test_extract_relations_from_chunk_applies_threshold(self) -> None:
        chunk = PdfStructuredChunk(
            source_file="doc.pdf",
            page=3,
            chapter="CAPITOLUL 1",
            section="1.1",
            chunk_id="chunk-rel-3",
            text="Aspirina trateaza boala.",
        )
        entities = [
            MedicalEntity(
                entity_type="drug",
                mention_text="aspirina",
                canonical_form="aspirina",
                confidence=0.7,
                source_file="doc.pdf",
                page=3,
                chunk_id="chunk-rel-3",
            ),
            MedicalEntity(
                entity_type="disease",
                mention_text="boala",
                canonical_form="boala",
                confidence=0.7,
                source_file="doc.pdf",
                page=3,
                chunk_id="chunk-rel-3",
            ),
        ]

        relations = extract_relations_from_chunk(chunk, entities, min_confidence=0.9)
        self.assertEqual(relations, [])


if __name__ == "__main__":
    unittest.main()
