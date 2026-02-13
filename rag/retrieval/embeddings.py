from __future__ import annotations

from sentence_transformers import SentenceTransformer


_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(_MODEL_NAME)
    return _model


def vector_size() -> int:
    return _get_model().get_sentence_embedding_dimension()


def embed_texts(texts: list[str]) -> list[list[float]]:
    vectors = _get_model().encode(texts, convert_to_tensor=False, normalize_embeddings=True)
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    vector = _get_model().encode([text], convert_to_tensor=False, normalize_embeddings=True)[0]
    return vector.tolist()

