from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from config.settings import QDRANT_URL, QDRANT_API_KEY, QDRANT_COLLECTION

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

COLLECTION = QDRANT_COLLECTION

