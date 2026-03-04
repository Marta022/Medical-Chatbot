from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from models import MedicalEntity, RetrievalResult
from rag.retrieval import retriever


class TestRetriever(unittest.TestCase):
    def test_retrieve_top_similar_maps_hits(self) -> None:
        fake_hit = SimpleNamespace(
            score=0.9,
            payload={
                "title": "A",
                "text": "alpha",
                "source": "unit",
                "source_file": "doc.pdf",
                "page": 4,
                "section": "2.1",
                "chunk_id": "chunk-4",
            },
        )
        with patch("rag.retrieval.retriever.embed_query", return_value=[0.1]) as embed_mock:
            with patch("rag.retrieval.retriever.client.search", return_value=[fake_hit]) as search_mock:
                result = retriever.retrieve_top_similar("q", top_k=1)

        embed_mock.assert_called_once()
        search_mock.assert_called_once()
        self.assertIsInstance(result, RetrievalResult)
        self.assertEqual(len(result.hits), 1)
        self.assertEqual(result.hits[0].title, "A")
        self.assertEqual(result.hits[0].text, "alpha")
        self.assertEqual(result.hits[0].source, "unit")
        self.assertEqual(result.hits[0].source_file, "doc.pdf")
        self.assertEqual(result.hits[0].page, 4)
        self.assertEqual(result.hits[0].section, "2.1")
        self.assertEqual(result.hits[0].chunk_id, "chunk-4")

    def test_retrieve_hybrid_merges_vector_and_graph_hits(self) -> None:
        vector_hit = SimpleNamespace(
            score=0.9,
            payload={"title": "Vector A", "text": "alpha", "source": "unit"},
        )
        graph_client = SimpleNamespace(
            execute=lambda _query, _params=None: [
                {
                    "source_entity": "myocardial infarction",
                    "relation_label": "DISEASE_HAS_SYMPTOM",
                    "target_entity": "durere toracica",
                    "source_file": "doc.pdf",
                    "page": 7,
                    "chunk_id": "chunk-7",
                    "confidence": 0.8,
                }
            ],
            close=lambda: None,
        )
        extracted = [
            MedicalEntity(
                entity_type="disease",
                mention_text="mi",
                canonical_form="myocardial infarction",
                confidence=0.9,
                source_file="query",
                page=0,
                chunk_id="query",
            )
        ]

        with patch("rag.retrieval.retriever.embed_query", return_value=[0.1]):
            with patch("rag.retrieval.retriever.client.search", return_value=[vector_hit]):
                with patch("rag.retrieval.retriever.load_disease_terms", return_value=set()):
                    with patch("rag.retrieval.retriever.extract_entities_from_chunk", return_value=extracted):
                        with patch("rag.retrieval.retriever.get_graph_client", return_value=graph_client):
                            result = retriever.retrieve_hybrid("q", top_k=3)

        self.assertEqual(len(result.hits), 2)
        self.assertEqual(result.hits[0].source, "unit")
        self.assertEqual(result.hits[1].source, "graph")

    def test_retrieve_top_similar_hybrid_mode_dispatch(self) -> None:
        expected = RetrievalResult(hits=[])
        with patch("rag.retrieval.retriever.retrieve_hybrid", return_value=expected) as hybrid_mock:
            result = retriever.retrieve_top_similar("q", top_k=2, retrieval_mode="hybrid")
        hybrid_mock.assert_called_once()
        self.assertIs(result, expected)

    def test_retrieve_hybrid_applies_policy_controls(self) -> None:
        vector_hit = SimpleNamespace(
            score=0.6,
            payload={"title": "Vector A", "text": "alpha", "source": "unit"},
        )
        graph_rows = [
            {
                "source_entity": "myocardial infarction",
                "relation_label": "DISEASE_HAS_SYMPTOM",
                "target_entity": "durere toracica",
                "source_file": "doc.pdf",
                "page": 7,
                "chunk_id": "chunk-7",
                "confidence": 0.8,
            }
        ]

        class FakeGraphClient:
            def __init__(self) -> None:
                self.calls: list[dict[str, str | int]] = []

            def execute(self, _query: str, params: dict[str, str | int] | None = None) -> list[dict[str, object]]:
                self.calls.append(params or {})
                return graph_rows

            def close(self) -> None:
                return None

        graph_client = FakeGraphClient()
        extracted = [
            MedicalEntity(
                entity_type="disease",
                mention_text="mi",
                canonical_form="myocardial infarction",
                confidence=0.9,
                source_file="query",
                page=0,
                chunk_id="query",
            )
        ]

        with patch("rag.retrieval.retriever.embed_query", return_value=[0.1]):
            with patch("rag.retrieval.retriever.client.search", return_value=[vector_hit]):
                with patch("rag.retrieval.retriever.load_disease_terms", return_value=set()):
                    with patch("rag.retrieval.retriever.extract_entities_from_chunk", return_value=extracted):
                        with patch("rag.retrieval.retriever.get_graph_client", return_value=graph_client):
                            result = retriever.retrieve_hybrid(
                                "q",
                                top_k=2,
                                filter_by={
                                    "__graph_depth": "2",
                                    "__vector_weight": "1.0",
                                    "__graph_weight": "0.5",
                                },
                            )

        self.assertEqual(len(graph_client.calls), 2)
        self.assertEqual(result.hits[0].source, "unit")
