"""CLI entrypoint and command router for the project.

Quick structure map:
- `chat`: runs the orchestration loop (guardrails -> retrieval -> LLM -> evaluator).
- `ingest`: pushes structured datasets (JSON/CSV) and corpus files (PDF/Markdown) into Qdrant.
- `extract-markdown`: converts PDF pages to markdown artifacts used by the ingest flow.
- `eval`: runs smoke evaluation checks.

This file should stay thin: parse arguments, validate startup constraints, then delegate
to domain modules (`knowledge`, `rag`, `agent`).
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
from dataclasses import replace
from pathlib import Path

from agent.benchmarking.benchmark import (
    DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH,
    DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
    run_evaluation_smoke,
    run_retrieval_benchmark,
)
from agent.orchestrator.chat_loop import run_chat_loop
from config.logging_config import new_correlation_id, setup_logging
from config.settings import (
    SETTINGS,
    SUPPORTED_CHUNKING_STRATEGIES,
    SUPPORTED_LLM_PROVIDERS,
    SUPPORTED_RETRIEVAL_MODES,
    ensure_startup_valid,
)
from knowledge.qdrant.ingest import ingest
from models.serde import serialize_to_json_compatible
from rag.chunking.load_documents import discover_markdown_paths, extract_pdf_to_markdown
from rag.retrieval.quality_report import build_quality_report

logger = logging.getLogger(__name__)


def _env_markdown_paths() -> list[str]:
    """Return markdown paths configured via INGEST_MARKDOWN_PATHS env var.

    The value is a semicolon- or comma-separated list of paths.
    """

    raw = os.getenv("INGEST_MARKDOWN_PATHS", "").strip()
    if not raw:
        return []
    # Support both ';' and ',' as separators.
    for separator in (";", ","):
        raw = raw.replace(separator, " ")
    return [part for part in (item.strip() for item in raw.split()) if part]


def _default_markdown_paths() -> list[str]:
    """Resolve default markdown corpus paths for ingest.

    Preference order:
    1) Explicit INGEST_MARKDOWN_PATHS environment variable.
    2) Auto-discovered markdown files in the dataset directory.
    """

    env_paths = _env_markdown_paths()
    if env_paths:
        return env_paths
    return discover_markdown_paths()


def _safe_model_suffix() -> str:
    """Return a filesystem-safe suffix for the current primary LLM model."""

    if SETTINGS.llm_provider == "openai":
        raw = SETTINGS.openai_model
    elif SETTINGS.llm_provider == "ollama":
        raw = SETTINGS.ollama_model
    else:
        raw = SETTINGS.qwen_model
    cleaned = re.sub(r"[^0-9A-Za-z_-]+", "", raw or "").strip("_-")
    return cleaned


def _next_benchmark_output_path() -> str:
    """Compute next benchmark output path as output_v<N>_<model>.txt.

    Scans existing files in the output directory and increments N.
    """

    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    max_index = 0
    pattern = re.compile(r"^output_v(\d+)")
    for path in output_dir.glob("output_v*.txt"):
        match = pattern.match(path.name)
        if not match:
            continue
        try:
            value = int(match.group(1))
        except ValueError:
            continue
        if value > max_index:
            max_index = value

    next_index = max_index + 1
    suffix = _safe_model_suffix()
    if suffix:
        filename = f"output_v{next_index}_{suffix}.txt"
    else:
        filename = f"output_v{next_index}.txt"
    return str(output_dir / filename)


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
        "--markdown-path",
        action="append",
        default=None,
        help="Markdown corpus path for direct ingest (for example data/dataset/cap_1_2_3.md). Repeat to include multiple files.",
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
    ingest_parser.add_argument(
        "--quality-report",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Emit ingestion/retrieval quality diagnostics after ingest",
    )
    ingest_parser.add_argument(
        "--quality-report-path",
        default="",
        help="Optional JSON output path for quality diagnostics report",
    )
    ingest_parser.add_argument(
        "--quality-keyword",
        action="append",
        default=None,
        help="Keyword probe for chunk-level lookup in quality report. Repeat to include multiple values.",
    )
    ingest_parser.add_argument(
        "--quality-keyword-limit",
        type=int,
        default=5,
        help="Maximum number of chunk matches to include per keyword in quality report",
    )

    extract_parser = subparsers.add_parser(
        "extract-markdown",
        help="Extract PDF pages to markdown with page-level LLM cleanup",
    )
    extract_parser.add_argument(
        "--pdf-path",
        default=SETTINGS.dataset_primary_pdf_path,
        help="Input PDF path to process",
    )
    extract_parser.add_argument(
        "--start-page",
        type=int,
        default=6,
        help="Human page number to start processing from (inclusive)",
    )
    extract_parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help="Optional human page number to stop at (inclusive)",
    )
    extract_parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where page markdown files and merged document are written",
    )
    extract_parser.add_argument(
        "--max-pages-per-run",
        type=int,
        default=0,
        help="Optional processing cap for batching long PDFs (0 means no cap)",
    )
    extract_parser.add_argument(
        "--provider",
        choices=sorted(SUPPORTED_LLM_PROVIDERS),
        default=SETTINGS.llm_provider,
        help="LLM provider used for page-level markdown cleanup",
    )

    eval_parser = subparsers.add_parser("eval", help="Run evaluation checks")
    eval_parser.add_argument(
        "--benchmark",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run benchmark validation against grile dataset and answer key (default: false)",
    )
    eval_parser.add_argument(
        "--benchmark-json-path",
        default=DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
        help="Path to benchmark grile JSON dataset",
    )
    eval_parser.add_argument(
        "--answer-key-path",
        default=DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH,
        help="Path to benchmark answer key (txt/json)",
    )
    eval_parser.add_argument(
        "--benchmark-top-k",
        type=int,
        default=SETTINGS.default_top_k,
        help="Retriever top_k used during benchmark question runs",
    )
    eval_parser.add_argument(
        "--benchmark-limit",
        type=int,
        default=0,
        help="Optional max number of benchmark items to evaluate (0 means all)",
    )
    eval_parser.add_argument(
        "--benchmark-use-guardrail",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Keep guardrail enabled during benchmark (default disables it for cleaner scoring)",
    )
    eval_parser.add_argument(
        "--benchmark-output",
        default="",
        help=(
            "File path where benchmark logs and metrics are saved. "
            "If omitted, a path like output/output_v<N>_<model>.txt is used."
        ),
    )
    return parser


def main() -> None:
    setup_logging()
    new_correlation_id()
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "chat":
        ensure_startup_valid(command=args.command)
        chat_filters = {
            "__retrieval_mode": str(args.retrieval_mode),
            "__graph_depth": str(args.graph_depth),
            "__vector_weight": str(args.vector_weight),
            "__graph_weight": str(args.graph_weight),
        }
        run_chat_loop(top_k=args.top_k, filters=chat_filters)
        return

    if args.command == "ingest":
        ingest_settings = replace(
            SETTINGS,
            chunking_strategy=args.chunking_strategy,
            semantic_use_llamaindex=args.semantic_use_llamaindex,
        )
        ensure_startup_valid(command=args.command, settings=ingest_settings)
        default_markdown_paths = _default_markdown_paths()
        corpus_paths: list[str]
        if args.skip_pdf_ingest:
            corpus_paths = []
        else:
            explicit_paths: list[str] = []
            if args.markdown_path:
                explicit_paths.extend(args.markdown_path)
            if args.pdf_path:
                explicit_paths.extend(args.pdf_path)
            corpus_paths = explicit_paths if explicit_paths else default_markdown_paths
        inserted = ingest(
            args.json_path,
            args.csv_path,
            chunking_strategy=args.chunking_strategy,
            semantic_chunk_max_chars=args.semantic_chunk_max_chars,
            semantic_use_llamaindex=args.semantic_use_llamaindex,
            pdf_paths=corpus_paths,
            include_structured_sources=not args.pdf_only,
            graph_ingest_enabled=args.graph_ingest,
            relation_min_confidence=args.relation_min_confidence,
            chunk_min_chars=SETTINGS.chunk_min_chars,
            chunk_min_words=SETTINGS.chunk_min_words,
            list_chunk_min_words=SETTINGS.list_chunk_min_words,
        )
        logger.info("Inserted into Qdrant: %s", inserted)
        if args.quality_report:
            report = build_quality_report(
                pdf_paths=corpus_paths,
                chunking_strategy=args.chunking_strategy,
                semantic_chunk_max_chars=args.semantic_chunk_max_chars,
                semantic_use_llamaindex=args.semantic_use_llamaindex,
                keyword_queries=args.quality_keyword,
                keyword_limit=args.quality_keyword_limit,
                top_k=SETTINGS.default_top_k,
            )
            if args.quality_report_path:
                output_path = Path(args.quality_report_path)
                output_path.write_text(
                    json.dumps(report, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                logger.info("Quality report written to %s", output_path)
            else:
                logger.info(json.dumps(report, ensure_ascii=False, indent=2))
        return

    if args.command == "eval":
        ensure_startup_valid(command=args.command)
        benchmark_output_path: Path | None = None
        if args.benchmark:
            if args.benchmark_output:
                benchmark_output_path = Path(args.benchmark_output)
            else:
                benchmark_output_path = Path(_next_benchmark_output_path())
            benchmark_output_path.parent.mkdir(parents=True, exist_ok=True)
            result = run_retrieval_benchmark(
                benchmark_json_path=args.benchmark_json_path,
                answer_key_path=args.answer_key_path,
                top_k=args.benchmark_top_k,
                language="ro",
                limit=(args.benchmark_limit if args.benchmark_limit > 0 else None),
                use_guardrail=args.benchmark_use_guardrail,
            )
        else:
            result = run_evaluation_smoke()
        payload = serialize_to_json_compatible(result)
        if benchmark_output_path is not None:
            benchmark_output_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            logger.info("Benchmark report written to %s", benchmark_output_path)
        logger.info(json.dumps(payload, ensure_ascii=False, indent=2))
        return

    if args.command == "extract-markdown":
        extraction_settings = replace(SETTINGS, llm_provider=args.provider)
        ensure_startup_valid(command=args.command, settings=extraction_settings)
        result = extract_pdf_to_markdown(
            pdf_path=args.pdf_path,
            output_dir=args.output_dir,
            start_page=args.start_page,
            end_page=args.end_page,
            max_pages_per_run=(args.max_pages_per_run if args.max_pages_per_run > 0 else None),
            provider=args.provider,
        )
        logger.info(json.dumps(result, ensure_ascii=False, indent=2))
        return

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
