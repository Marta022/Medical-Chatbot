from __future__ import annotations

from qdrant_client.models import FieldCondition, Filter, MatchValue

from knowledge.qdrant.client import COLLECTION, client
from models import RetrievalHit, RetrievalResult
from rag.retrieval.embeddings import embed_query


def _build_filter(filter_by: dict[str, str] | None) -> Filter | None:
    if not filter_by:
        return None
    conditions = [
        FieldCondition(key=key, match=MatchValue(value=value))
        for key, value in filter_by.items()
        if value is not None
    ]
    if not conditions:
        return None
    return Filter(must=conditions)


def retrieve_top_similar(
    input_message: str,
    top_k: int = 5,
    filter_by: dict[str, str] | None = None,
) -> RetrievalResult:
    query_vector = embed_query(input_message)
    payload_filter = _build_filter(filter_by)

    hits = client.search(
        collection_name=COLLECTION,
        query_vector=query_vector,
        limit=top_k,
        with_payload=True,
        query_filter=payload_filter,
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
