# TODO(remove-shim): remove after P2 stabilization.
import logging

from config.logging_config import new_correlation_id, setup_logging
from config.settings import SETTINGS
from knowledge.qdrant.ingest import ingest

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    setup_logging()
    new_correlation_id()
    count = ingest(SETTINGS.dataset_json_path, SETTINGS.dataset_csv_path)
    logger.info("Inserted into Qdrant: %s", count)
