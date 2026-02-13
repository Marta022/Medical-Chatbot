from __future__ import annotations

from models import RetrievalHit, RetrievalResult

from knowledge.qdrant.client import COLLECTION, client
from rag.retrieval.embeddings import embed_query


def retrieve_top_similar(
    input_message: str,
    top_k: int = 5,
) -> RetrievalResult:
    query_vector = embed_query(input_message)

    hits = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
    )

    retrieval_hits: list[RetrievalHit] = []
    for hit in hits:
        payload = hit.payload or {}
        retrieval_hits.append(
            RetrievalHit(
                title=str(payload.get("title", "unknown")).strip(),
                text=str(payload.get("text", "")).strip(),
                score=float(hit.score),
                source=str(payload.get("source", "unknown")),
            )
        )

    return RetrievalResult(hits=retrieval_hits)

