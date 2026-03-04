from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from knowledge.graph.gitnexus import build_gitnexus_payload, build_gitnexus_payload_safe


class TestGitNexus(unittest.TestCase):
    def test_build_gitnexus_payload_maps_nodes_edges_and_links(self) -> None:
        graph_client = SimpleNamespace(
            execute=lambda _query, _params=None: [
                {
                    "source_id": "a1",
                    "source_label": "myocardial infarction",
                    "source_type": "disease",
                    "target_id": "b1",
                    "target_label": "durere toracica",
                    "target_type": "symptom",
                    "relation_label": "DISEASE_HAS_SYMPTOM",
                    "source_file": "doc.pdf",
                    "page": 12,
                    "chunk_id": "chunk-12",
                    "confidence": 0.88,
                }
            ],
            close=lambda: None,
        )
        with patch("knowledge.graph.gitnexus.get_graph_client", return_value=graph_client):
            with patch("knowledge.graph.gitnexus.SETTINGS", SimpleNamespace(gitnexus_base_url="http://nexus:8088")):
                payload = build_gitnexus_payload(query="mi", limit=5)

        self.assertEqual(payload["query"], "mi")
        self.assertEqual(len(payload["nodes"]), 2)
        self.assertEqual(len(payload["edges"]), 1)
        self.assertIn("source://doc.pdf", payload["edges"][0]["source_link"])
        self.assertIn("/graph?query=mi", payload["viewer_url"])

    def test_build_gitnexus_payload_safe_returns_disabled_when_off(self) -> None:
        with patch("knowledge.graph.gitnexus.SETTINGS", SimpleNamespace(gitnexus_enabled=False)):
            payload = build_gitnexus_payload_safe(query="x", limit=3)
        self.assertEqual(payload["status"], "disabled")
        self.assertEqual(payload["nodes"], [])
        self.assertEqual(payload["edges"], [])


if __name__ == "__main__":
    unittest.main()
