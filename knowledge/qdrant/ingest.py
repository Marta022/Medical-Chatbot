from __future__ import annotations

from qdrant_client.models import PointStruct

from rag.chunking.load_documents import load_medical_items
from rag.retrieval.embeddings import embed_texts, vector_size

from knowledge.qdrant.client import COLLECTION, client, ensure_collection


def ingest(json_path: str, csv_path: str) -> int:
    items = load_medical_items(json_path, csv_path)
    ensure_collection(vector_size())

    points: list[PointStruct] = []
    for idx, item in enumerate(items):
        text = f"{item.title}\n{item.description}"
        vector = embed_texts([text])[0]
        payload = {
            "text": text,
            "title": item.title,
            "source": item.source,
            "category": item.category,
        }
        points.append(PointStruct(id=idx, vector=vector, payload=payload))

    client.upsert(collection_name=COLLECTION, points=points)
    return len(points)

