from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from models import RetrievalResult
from rag.retrieval import retriever


class TestRetriever(unittest.TestCase):
    def test_retrieve_top_similar_maps_hits(self) -> None:
        fake_hit = SimpleNamespace(
            score=0.9,
            payload={"title": "A", "text": "alpha", "source": "unit"},
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
