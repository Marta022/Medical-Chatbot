from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from rag.retrieval import embeddings


class TestEmbeddings(unittest.TestCase):
    def setUp(self) -> None:
        embeddings._model = None
        embeddings._use_fallback = False
        embeddings._openai_client = None

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

        with patch.dict("os.environ", {"EMBEDDING_PROVIDER": "sentence-transformers"}, clear=False):
            with patch("rag.retrieval.embeddings._sentence_transformer_cls", return_value=lambda *args, **kwargs: fake_model):
                size = embeddings.vector_size()
                self.assertEqual(size, 3)

                vectors = embeddings.embed_texts(["a"])
                self.assertEqual(vectors, [[0.1, 0.2, 0.3]])

                vector = embeddings.embed_query("q")
                self.assertEqual(vector, [0.1, 0.2, 0.3])

    def test_openai_embeddings_backend(self) -> None:
        fake_response = MagicMock()
        fake_response.data = [
            MagicMock(embedding=[0.4, 0.5, 0.6]),
            MagicMock(embedding=[0.7, 0.8, 0.9]),
        ]
        fake_client = MagicMock()
        fake_client.embeddings.create.return_value = fake_response

        with patch.dict(
            "os.environ",
            {
                "EMBEDDING_PROVIDER": "openai",
                "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
            },
            clear=False,
        ):
            with patch("rag.retrieval.embeddings.OpenAI", return_value=fake_client):
                self.assertEqual(embeddings.vector_size(), 1536)
                vectors = embeddings.embed_texts(["a", "b"])
                self.assertEqual(vectors, [[0.4, 0.5, 0.6], [0.7, 0.8, 0.9]])
                vector = embeddings.embed_query("q")
                self.assertEqual(vector, [0.4, 0.5, 0.6])
                self.assertFalse(embeddings.using_fallback_embeddings())


if __name__ == "__main__":
    unittest.main()
