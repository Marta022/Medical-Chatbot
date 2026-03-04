from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from knowledge.graph.schema import ensure_graph_schema, graph_schema_statements


class TestGraphSchema(unittest.TestCase):
    def test_graph_schema_contains_required_predicates(self) -> None:
        schema = "\n".join(graph_schema_statements())
        self.assertIn("CREATE NODE TABLE IF NOT EXISTS Entity", schema)
        self.assertIn("CREATE NODE TABLE IF NOT EXISTS SourceChunk", schema)
        self.assertIn("CREATE REL TABLE IF NOT EXISTS DISEASE_HAS_SYMPTOM", schema)
        self.assertIn("CREATE REL TABLE IF NOT EXISTS DRUG_TREATS_DISEASE", schema)
        self.assertIn("CREATE REL TABLE IF NOT EXISTS CONDITION_CAUSES_SYMPTOM", schema)
        self.assertIn("CREATE REL TABLE IF NOT EXISTS DISEASE_DIFFERS_FROM_DISEASE", schema)

    def test_graph_schema_relations_include_provenance_fields(self) -> None:
        schema = "\n".join(graph_schema_statements())
        self.assertIn("source_file STRING", schema)
        self.assertIn("page INT64", schema)
        self.assertIn("chunk_id STRING", schema)
        self.assertIn("confidence DOUBLE", schema)

    def test_ensure_graph_schema_executes_all_statements(self) -> None:
        graph_client = MagicMock()
        ensure_graph_schema(graph_client)
        self.assertEqual(graph_client.execute.call_count, len(graph_schema_statements()))


if __name__ == "__main__":
    unittest.main()
