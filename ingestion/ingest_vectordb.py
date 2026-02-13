# TODO(remove-shim): remove after P2 stabilization.
from config.settings import SETTINGS
from knowledge.qdrant.ingest import ingest


if __name__ == "__main__":
    count = ingest(SETTINGS.dataset_json_path, SETTINGS.dataset_csv_path)
    print(f"Inserted into Qdrant: {count}")

