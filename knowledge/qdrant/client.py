from __future__ import annotations

from qdrant_client import QdrantClient
from qdrant_client.http import exceptions as qdrant_exceptions
from qdrant_client.models import Distance, VectorParams

from config.settings import SETTINGS

COLLECTION = SETTINGS.qdrant_collection

client = QdrantClient(
    url=SETTINGS.qdrant_url,
    api_key=SETTINGS.qdrant_api_key,
)


def ensure_collection(vector_dim: int) -> None:
    if not COLLECTION:
        raise ValueError("Qdrant collection name is empty")

    try:
        client.get_collection(collection_name=COLLECTION)
    except (
        qdrant_exceptions.UnexpectedResponse,
        qdrant_exceptions.ResponseHandlingException,
    ):
        client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
        )
