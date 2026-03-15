from __future__ import annotations

import hashlib
import logging
import os
from math import sqrt
from typing import Any

from openai import OpenAI

_MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
_model: Any | None = None
_use_fallback = False
_FALLBACK_DIM = 384
_openai_client: OpenAI | None = None
logger = logging.getLogger(__name__)

_OPENAI_EMBEDDING_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


def _embedding_provider() -> str:
    return os.getenv("EMBEDDING_PROVIDER", "sentence-transformers").strip().lower()


def _openai_embedding_model() -> str:
    return os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small").strip()


def _sentence_transformer_cls() -> Any:
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer


def _get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


def _embed_with_openai(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    response = _get_openai_client().embeddings.create(
        model=_openai_embedding_model(),
        input=texts,
    )
    return [list(item.embedding) for item in response.data]


def _get_model() -> Any:
    global _model, _use_fallback
    if _use_fallback:
        raise RuntimeError("Using fallback embeddings backend")

    if _model is None:
        sentence_transformer_cls = _sentence_transformer_cls()
        allow_download = os.getenv("ALLOW_MODEL_DOWNLOAD", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        try:
            # Prefer local cache so offline/blocked environments do not hang on retries.
            _model = sentence_transformer_cls(_MODEL_NAME, local_files_only=True)
        except Exception:
            if allow_download:
                _model = sentence_transformer_cls(_MODEL_NAME)
            else:
                _use_fallback = True
                logger.warning(
                    "Embedding model '%s' not found in local cache. Falling back to "
                    "deterministic hash embeddings. Set ALLOW_MODEL_DOWNLOAD=true "
                    "to enable online model download.",
                    _MODEL_NAME,
                )
                raise RuntimeError("Using fallback embeddings backend")
    return _model


def vector_size() -> int:
    if _embedding_provider() == "openai":
        return _OPENAI_EMBEDDING_DIMS.get(_openai_embedding_model(), 1536)
    try:
        return _get_model().get_sentence_embedding_dimension()
    except RuntimeError:
        return _FALLBACK_DIM


def using_fallback_embeddings() -> bool:
    return _embedding_provider() != "openai" and _use_fallback


def _hash_embedding(text: str, dim: int = _FALLBACK_DIM) -> list[float]:
    values: list[float] = []
    seed = text.encode("utf-8")
    counter = 0
    while len(values) < dim:
        digest = hashlib.sha256(seed + counter.to_bytes(4, "little")).digest()
        for byte in digest:
            values.append((byte / 255.0) - 0.5)
            if len(values) == dim:
                break
        counter += 1

    norm = sqrt(sum(value * value for value in values))
    if norm == 0:
        return values
    return [value / norm for value in values]


def _embed_fallback(texts: list[str]) -> list[list[float]]:
    return [_hash_embedding(text) for text in texts]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if _embedding_provider() == "openai":
        return _embed_with_openai(texts)
    try:
        vectors = _get_model().encode(texts, convert_to_tensor=False, normalize_embeddings=True)
        return vectors.tolist()
    except RuntimeError:
        return _embed_fallback(texts)


def embed_query(text: str) -> list[float]:
    if _embedding_provider() == "openai":
        vectors = _embed_with_openai([text])
        return vectors[0] if vectors else []
    try:
        vector = _get_model().encode([text], convert_to_tensor=False, normalize_embeddings=True)[0]
        return vector.tolist()
    except RuntimeError:
        return _hash_embedding(text)
