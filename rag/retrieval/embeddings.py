"""Embedding backends and fallback behavior for retrieval."""

from __future__ import annotations

import logging
import os
from typing import Any

from openai import OpenAI

logger = logging.getLogger(__name__)
MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
DEFAULT_EMBEDDING_PROVIDER = "sentence-transformers"
OPENAI_EMBEDDING_PROVIDER = "openai"
ALLOW_MODEL_DOWNLOAD_ENV = "ALLOW_MODEL_DOWNLOAD"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"
OPENAI_EMBEDDING_MODEL_ENV = "OPENAI_EMBEDDING_MODEL"
DEFAULT_OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
ALLOW_DOWNLOAD_TRUTHY_VALUES = {"1", "true", "yes", "on"}
_model: Any | None = None
_openai_client: OpenAI | None = None

_OPENAI_EMBEDDING_DIMS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


def _embedding_provider() -> str:
    """Return the active embeddings backend from environment configuration."""

    return os.getenv("EMBEDDING_PROVIDER", DEFAULT_EMBEDDING_PROVIDER).strip().lower()


def _openai_embedding_model() -> str:
    """Return the configured OpenAI embedding model name."""

    return os.getenv(OPENAI_EMBEDDING_MODEL_ENV, DEFAULT_OPENAI_EMBEDDING_MODEL).strip()


def _sentence_transformer_cls() -> Any:
    """Import and return the SentenceTransformer class lazily."""

    from sentence_transformers import SentenceTransformer

    return SentenceTransformer


def _get_openai_client() -> OpenAI:
    """Create and cache the OpenAI client used for embeddings."""

    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv(OPENAI_API_KEY_ENV))
    return _openai_client


def _embed_with_openai(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts with the OpenAI embeddings API."""

    if not texts:
        return []
    response = _get_openai_client().embeddings.create(
        model=_openai_embedding_model(),
        input=texts,
    )
    return [list(item.embedding) for item in response.data]


def _get_model() -> Any:
    """Load and cache the sentence-transformers backend."""

    global _model

    if _model is None:
        sentence_transformer_cls = _sentence_transformer_cls()
        allow_download = (
            os.getenv(ALLOW_MODEL_DOWNLOAD_ENV, "").strip().lower() in ALLOW_DOWNLOAD_TRUTHY_VALUES
        )
        try:
            # Prefer local cache so offline/blocked environments do not hang on retries.
            _model = sentence_transformer_cls(MODEL_NAME, local_files_only=True)
        except Exception as exc:
            if allow_download:
                logger.info(
                    "Loading embedding model '%s' with downloads enabled after cache miss.",
                    MODEL_NAME,
                )
                _model = sentence_transformer_cls(MODEL_NAME)
            else:
                raise RuntimeError(
                    "Embedding model not available in local cache and downloads are disabled. "
                    "Set ALLOW_MODEL_DOWNLOAD=true or provide local model artifacts. "
                    f"Loader error: {exc}"
                )
    return _model


def vector_size() -> int:
    """Return the current embedding vector size for the active backend."""

    if _embedding_provider() == OPENAI_EMBEDDING_PROVIDER:
        return _OPENAI_EMBEDDING_DIMS.get(_openai_embedding_model(), 1536)
    return _get_model().get_sentence_embedding_dimension()


def using_fallback_embeddings() -> bool:
    """Backward-compatible helper: deterministic fallback mode is disabled."""

    return False


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using the configured backend."""

    if _embedding_provider() == OPENAI_EMBEDDING_PROVIDER:
        return _embed_with_openai(texts)
    vectors = _get_model().encode(texts, convert_to_tensor=False, normalize_embeddings=True)
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    """Embed a single query string using the configured backend."""

    if _embedding_provider() == OPENAI_EMBEDDING_PROVIDER:
        vectors = _embed_with_openai([text])
        return vectors[0] if vectors else []
    vector = _get_model().encode([text], convert_to_tensor=False, normalize_embeddings=True)[0]
    return vector.tolist()
