# TODO(remove-shim): remove after P2 stabilization.
import logging

from config.logging_config import new_correlation_id, setup_logging
from config.settings import SETTINGS
from knowledge.qdrant.ingest import ingest
from rag.chunking.load_documents import discover_pdf_paths

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    setup_logging()
    new_correlation_id()
    count = ingest(
        SETTINGS.dataset_json_path,
        SETTINGS.dataset_csv_path,
        chunking_strategy=SETTINGS.chunking_strategy,
        semantic_chunk_max_chars=SETTINGS.semantic_chunk_max_chars,
        semantic_use_llamaindex=SETTINGS.semantic_use_llamaindex,
        pdf_paths=discover_pdf_paths(excluded_paths=[SETTINGS.dataset_validation_pdf_path]),
        include_structured_sources=False,
        graph_ingest_enabled=SETTINGS.graph_ingest_enabled,
        relation_min_confidence=SETTINGS.relation_min_confidence,
    )
    logger.info("Inserted into Qdrant: %s", count)
