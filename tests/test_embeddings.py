from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from rag.retrieval import embeddings


class TestEmbeddings(unittest.TestCase):
    def setUp(self) -> None:
        embeddings._model = None
        embeddings._use_fallback = False

    def test_vector_size_and_embed(self) -> None:
        class FakeVector:
            def __init__(self, data: list[float]):
                self._data = data

            def tolist(self) -> list[float]:
                return self._data

        class FakeArray:
            def __init__(self, data: list[list[float]]):
                self._data = data

            def tolist(self) -> list[list[float]]:
                return self._data

            def __getitem__(self, index: int) -> list[float]:
                return FakeVector(self._data[index])

        fake_model = MagicMock()
        fake_model.get_sentence_embedding_dimension.return_value = 3
        fake_model.encode.return_value = FakeArray([[0.1, 0.2, 0.3]])

        with patch("rag.retrieval.embeddings.SentenceTransformer", return_value=fake_model):
            size = embeddings.vector_size()
            self.assertEqual(size, 3)

            vectors = embeddings.embed_texts(["a"])
            self.assertEqual(vectors, [[0.1, 0.2, 0.3]])

            vector = embeddings.embed_query("q")
            self.assertEqual(vector, [0.1, 0.2, 0.3])


if __name__ == "__main__":
    unittest.main()
