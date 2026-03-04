from __future__ import annotations

import argparse
import json
import logging

from agent.evaluation.benchmark import run_evaluation_smoke
from agent.orchestrator.chat_loop import run_chat_loop
from config.logging_config import new_correlation_id, setup_logging
from config.settings import (
    SETTINGS,
    SUPPORTED_CHUNKING_STRATEGIES,
    SUPPORTED_RETRIEVAL_MODES,
    ensure_startup_valid,
)
from knowledge.qdrant.ingest import ingest
from rag.chunking.load_documents import discover_pdf_paths
from models.serde import serialize_to_json_compatible

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Medical chatbot CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    chat_parser = subparsers.add_parser("chat", help="Run interactive chat loop")
    chat_parser.add_argument(
        "--top-k",
        type=int,
        default=SETTINGS.default_top_k,
        help="Retrieval top_k",
    )
    chat_parser.add_argument(
        "--retrieval-mode",
        choices=sorted(SUPPORTED_RETRIEVAL_MODES),
        default=SETTINGS.retrieval_mode,
        help="Retrieval mode: vector or graph-hybrid",
    )
    chat_parser.add_argument(
        "--graph-depth",
        type=int,
        default=SETTINGS.graph_traversal_depth,
        help="Graph traversal depth for hybrid mode",
    )
    chat_parser.add_argument(
        "--vector-weight",
        type=float,
        default=SETTINGS.hybrid_vector_weight,
        help="Vector score weight in hybrid merge/rerank",
    )
    chat_parser.add_argument(
        "--graph-weight",
        type=float,
        default=SETTINGS.hybrid_graph_weight,
        help="Graph score weight in hybrid merge/rerank",
    )

    ingest_parser = subparsers.add_parser("ingest", help="Ingest datasets into Qdrant")
    ingest_parser.add_argument(
        "--json-path",
        default=SETTINGS.dataset_json_path,
        help="Path to JSON medical dataset",
    )
    ingest_parser.add_argument(
        "--csv-path",
        default=SETTINGS.dataset_csv_path,
        help="Path to CSV medical dataset",
    )
    ingest_parser.add_argument(
        "--pdf-path",
        action="append",
        default=None,
        help="PDF corpus path. Repeat to include multiple files.",
    )
    ingest_parser.add_argument(
        "--skip-pdf-ingest",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Skip PDF corpus ingestion and ingest only JSON/CSV datasets",
    )
    ingest_parser.add_argument(
        "--pdf-only",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Ingest only PDF corpus (skip JSON/CSV sources)",
    )
    ingest_parser.add_argument(
        "--chunking-strategy",
        default=SETTINGS.chunking_strategy,
        choices=sorted(SUPPORTED_CHUNKING_STRATEGIES),
        help="Chunking strategy used before embedding",
    )
    ingest_parser.add_argument(
        "--semantic-chunk-max-chars",
        type=int,
        default=SETTINGS.semantic_chunk_max_chars,
        help="Maximum semantic chunk size in characters for fallback mode",
    )
    ingest_parser.add_argument(
        "--semantic-use-llamaindex",
        action=argparse.BooleanOptionalAction,
        default=SETTINGS.semantic_use_llamaindex,
        help="Enable LlamaIndex semantic splitter when available",
    )
    ingest_parser.add_argument(
        "--graph-ingest",
        action=argparse.BooleanOptionalAction,
        default=SETTINGS.graph_ingest_enabled,
        help="Enable graph ingestion into Kuzu after PDF chunk ingestion",
    )
    ingest_parser.add_argument(
        "--relation-min-confidence",
        type=float,
        default=SETTINGS.relation_min_confidence,
        help="Minimum confidence threshold for extracted graph relations",
    )

    subparsers.add_parser("eval", help="Run evaluation smoke check")
    return parser


def main() -> None:
    setup_logging()
    new_correlation_id()
    parser = _build_parser()
    args = parser.parse_args()

    ensure_startup_valid(command=args.command)

    if args.command == "chat":
        chat_filters = {
            "__retrieval_mode": str(args.retrieval_mode),
            "__graph_depth": str(args.graph_depth),
            "__vector_weight": str(args.vector_weight),
            "__graph_weight": str(args.graph_weight),
        }
        run_chat_loop(top_k=args.top_k, filters=chat_filters)
        return

    if args.command == "ingest":
        default_pdf_paths = discover_pdf_paths(
            excluded_paths=[SETTINGS.dataset_validation_pdf_path],
        )
        pdf_paths = (
            []
            if args.skip_pdf_ingest
            else (args.pdf_path if args.pdf_path is not None else default_pdf_paths)
        )
        inserted = ingest(
            args.json_path,
            args.csv_path,
            chunking_strategy=args.chunking_strategy,
            semantic_chunk_max_chars=args.semantic_chunk_max_chars,
            semantic_use_llamaindex=args.semantic_use_llamaindex,
            pdf_paths=pdf_paths,
            include_structured_sources=not args.pdf_only,
            graph_ingest_enabled=args.graph_ingest,
            relation_min_confidence=args.relation_min_confidence,
        )
        logger.info("Inserted into Qdrant: %s", inserted)
        return

    if args.command == "eval":
        result = run_evaluation_smoke()
        payload = serialize_to_json_compatible(result)
        logger.info(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
