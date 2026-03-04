from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from knowledge.graph.ids import build_entity_id
from knowledge.graph.ingest import (
    ingest_pdf_chunks_to_graph,
    reconcile_entities,
    reconcile_relations,
)
from models.contracts import MedicalEntity, MedicalRelation, PdfStructuredChunk


class TestGraphIngest(unittest.TestCase):
    def test_reconcile_entities_deduplicates_by_type_and_canonical_form(self) -> None:
        first = MedicalEntity(
            entity_type="disease",
            mention_text="mi",
            canonical_form="myocardial infarction",
            confidence=0.8,
            source_file="a.pdf",
            page=1,
            chunk_id="c1",
        )
        second = MedicalEntity(
            entity_type="disease",
            mention_text="infarct miocardic",
            canonical_form="myocardial infarction",
            confidence=0.9,
            source_file="a.pdf",
            page=2,
            chunk_id="c2",
        )
        unique = reconcile_entities([first, second])
        self.assertEqual(len(unique), 1)
        self.assertEqual(unique[0].confidence, 0.9)

    def test_reconcile_relations_deduplicates_by_predicate_and_endpoints(self) -> None:
        source_id = build_entity_id("disease", "myocardial infarction")
        target_id = build_entity_id("symptom", "durere toracica")
        first = MedicalRelation(
            predicate="disease_has_symptom",
            source_entity_id=source_id,
            source_entity_type="disease",
            source_canonical_form="myocardial infarction",
            target_entity_id=target_id,
            target_entity_type="symptom",
            target_canonical_form="durere toracica",
            confidence=0.72,
            source_file="a.pdf",
            page=1,
            chunk_id="c1",
        )
        second = MedicalRelation(
            predicate="disease_has_symptom",
            source_entity_id=source_id,
            source_entity_type="disease",
            source_canonical_form="myocardial infarction",
            target_entity_id=target_id,
            target_entity_type="symptom",
            target_canonical_form="durere toracica",
            confidence=0.83,
            source_file="a.pdf",
            page=2,
            chunk_id="c2",
        )
        unique = reconcile_relations([first, second])
        self.assertEqual(len(unique), 1)
        self.assertEqual(unique[0].confidence, 0.83)

    def test_ingest_pdf_chunks_to_graph_generates_entities_and_relations(self) -> None:
        chunk_one = PdfStructuredChunk(
            source_file="doc.pdf",
            page=10,
            chapter="CAPITOLUL 1",
            section="1.1",
            chunk_id="chunk-10",
            text="Pacient cu MI si durere toracica. Aspirina trateaza aceasta afectiune.",
        )
        chunk_two = PdfStructuredChunk(
            source_file="doc.pdf",
            page=11,
            chapter="CAPITOLUL 1",
            section="1.2",
            chunk_id="chunk-11",
            text="Infarctul miocardic determina dispnee.",
        )

        graph_client = MagicMock()
        stats = ingest_pdf_chunks_to_graph(
            [chunk_one, chunk_two],
            disease_terms=set(),
            graph_client=graph_client,
        )

        self.assertEqual(stats["chunks"], 2)
        self.assertGreaterEqual(stats["entities"], 3)
        self.assertGreaterEqual(stats["mentions"], 3)
        self.assertGreaterEqual(stats["relations"], 2)

        calls = [str(call.args[0]) for call in graph_client.execute.call_args_list]
        self.assertTrue(any("CREATE NODE TABLE IF NOT EXISTS Entity" in call for call in calls))
        self.assertTrue(any("MERGE (e:Entity" in call for call in calls))
        self.assertTrue(any("MERGE (a)-[r:DISEASE_HAS_SYMPTOM]->(b)" in call for call in calls))


if __name__ == "__main__":
    unittest.main()
