from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import importlib
from models import MedicalItem


class TestQdrantIngest(unittest.TestCase):
    def test_ingest_builds_points(self) -> None:
        ingest_module = importlib.import_module("knowledge.qdrant.ingest")
        item = MedicalItem(title="A", description="B", source="json", category="C")

        with patch(
            "knowledge.qdrant.ingest.load_medical_items",
            return_value=[item],
        ):
            with patch(
                "knowledge.qdrant.ingest.chunk_text",
                return_value=["chunk1"],
            ):
                with patch(
                    "knowledge.qdrant.ingest.embed_texts",
                    return_value=[[0.1, 0.2]],
                ):
                    with patch(
                        "knowledge.qdrant.ingest.vector_size",
                        return_value=2,
                    ):
                        with patch("knowledge.qdrant.ingest.ensure_collection") as ensure_mock:
                            with patch("knowledge.qdrant.ingest.client", MagicMock()) as client_mock:
                                count = ingest_module.ingest("a.json", "b.csv")

        ensure_mock.assert_called_once_with(2)
        client_mock.upsert.assert_called_once()
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
