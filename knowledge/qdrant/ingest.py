from __future__ import annotations

import uuid

from qdrant_client.models import PointStruct

from knowledge.qdrant.client import COLLECTION, client, ensure_collection
from rag.chunking.load_documents import load_medical_items
from rag.chunking.strategies import chunk_text
from rag.retrieval.embeddings import embed_texts, vector_size


def build_point_id(
    source: str,
    title: str,
    category: str | None,
    chunk_text_value: str,
    chunk_index: int,
) -> str:
    payload = f"{source}|{title}|{category or ''}|{chunk_index}|{chunk_text_value}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, payload))


def ingest(json_path: str, csv_path: str, chunking_strategy: str = "section") -> int:
    items = load_medical_items(json_path, csv_path)
    ensure_collection(vector_size())

    points: list[PointStruct] = []
    for item in items:
        base_text = f"{item.title}\n{item.description}".strip()
        chunks = chunk_text(base_text, strategy=chunking_strategy)
        if not chunks:
            chunks = [base_text]

        vectors = embed_texts(chunks)
        for chunk_index, (chunk, vector) in enumerate(
            zip(chunks, vectors, strict=False),
            start=1,
        ):
            payload = {
                "text": chunk,
                "title": item.title,
                "source": item.source,
                "category": item.category,
                "chunk_index": chunk_index,
                "chunking_strategy": chunking_strategy,
            }
            point_id = build_point_id(
                item.source,
                item.title,
                item.category,
                chunk,
                chunk_index,
            )
            points.append(PointStruct(id=point_id, vector=vector, payload=payload))

    client.upsert(collection_name=COLLECTION, points=points)
    return len(points)
