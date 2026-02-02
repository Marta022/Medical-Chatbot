from qdrant_client.models import PointStruct
from ingestion.load_documents import load_medical_items
from ingestion.embed import embed_texts, vector_size
from vector_db.qdrant_client import client, ensure_collection, COLLECTION


def ingest(json_path, csv_path):
    items = load_medical_items(json_path, csv_path)

    ensure_collection(vector_size())

    points = []
    pid = 0

    for idx, item in enumerate(items):
        text = item["title"] + "\n" + item["description"]

        if idx < 3:
            print("\n==============================")
            print("ITEM", idx + 1, "TEXT FOR EMBEDDING:")
            print(text)
            print("==============================\n")

        vec = embed_texts([text])[0]

        payload = {
            "text": text,
            "title": item["title"],
            "source": item.get("source", "unknown"),
        }

        points.append(PointStruct(
            id=pid,
            vector=vec,
            payload=payload,
        ))
        pid += 1

    client.upsert(collection_name=COLLECTION, points=points)
    print("Inserted into Qdrant:", len(points))


if __name__ == "__main__":
    ingest("data/disease_database.json", "data/dataset - Sheet1.csv")
    client.close() 
