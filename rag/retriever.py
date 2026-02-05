from ingestion.embed import embed_query
from vector_db.qdrant_client import client, COLLECTION

def retrieve_top_similar_descriptions(input_message, top_k=5):
    qvec = embed_query(input_message)

    hits = client.search(
        collection_name=COLLECTION,
        query_vector=qvec,
        limit=top_k,
        with_payload=True,
    )

    results = []
    titles = []

    for h in hits:
        payload = h.payload or {}
        title = payload.get("title", "unknown").strip()
        text = payload.get("text", "").strip()
        score = float(h.score)

        results.append(f"{text} ({score:.4f})")
        titles.append(title)

    return results, titles
