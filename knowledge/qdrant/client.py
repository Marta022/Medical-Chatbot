"""Qdrant client bootstrap and collection lifecycle helpers."""

from __future__ import annotations

import logging

from qdrant_client import QdrantClient
from qdrant_client.http import exceptions as qdrant_exceptions
from qdrant_client.models import Distance, VectorParams

from config.settings import SETTINGS

logger = logging.getLogger(__name__)
COLLECTION = SETTINGS.qdrant_collection
VECTOR_DISTANCE = Distance.COSINE

client = QdrantClient(
    url=SETTINGS.qdrant_url,
    api_key=SETTINGS.qdrant_api_key,
)


def ensure_collection(vector_dim: int) -> None:
    """Ensure the configured Qdrant collection exists with the expected vector size."""

    if not COLLECTION:
        raise ValueError("Qdrant collection name is empty")
    if vector_dim <= 0:
        raise ValueError("vector_dim must be greater than 0")

    try:
        client.get_collection(collection_name=COLLECTION)
        logger.info("Using existing Qdrant collection '%s'.", COLLECTION)
    except (
        qdrant_exceptions.UnexpectedResponse,
        qdrant_exceptions.ResponseHandlingException,
    ) as exc:
        logger.info(
            "Creating Qdrant collection '%s' after lookup failure: %s",
            COLLECTION,
            exc,
        )
        client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=vector_dim, distance=VECTOR_DISTANCE),
        )
