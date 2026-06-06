"""Standalone demo entrypoint for the first benchmark grid item.

This script is intentionally separate from `run.py` so the production CLI stays
unchanged while the benchmark demo can document each visible stage with logs.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Any

from agent.benchmarking.benchmark import (
    BENCHMARK_SYSTEM_PROMPT,
    DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH,
    DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
    RETRIEVAL_POOL_EXTRA,
    RETRIEVAL_POOL_MULTIPLIER,
    _benchmark_rejection_reason,
    _build_benchmark_context_block,
    _build_grila_prompt,
    _build_option_queries,
    _extract_benchmark_prediction,
    _rerank_benchmark_hits,
    _score_prediction,
    _serialize_retrieved_chunks,
    load_retrieval_answer_key,
    load_retrieval_benchmark_items,
)
from config.logging_config import new_correlation_id, setup_logging
from config.settings import SETTINGS, ensure_startup_valid
from models import LLMRequest, RetrievalHit
from models.serde import serialize_to_json_compatible

logger = logging.getLogger(__name__)

DEFAULT_DEMO_OUTPUT_PATH = "output/benchmark_demo_first_grid.json"
DEFAULT_DEMO_RETRIEVED_CONTEXT_COUNT = 3


def _quiet_transport_logs() -> None:
    """Hide per-request HTTP logs so demo output shows benchmark architecture."""

    for logger_name in ("httpx", "httpcore", "openai", "qdrant_client"):
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def _percent(value: object) -> str:
    """Format numeric metric values as percentages for demo logs."""

    if not isinstance(value, int | float):
        return "n/a"
    return f"{value * 100:.2f}%"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run benchmark demo on the first grid item")
    parser.add_argument(
        "--benchmark-json-path",
        default=DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
        help="Path to benchmark grile JSON dataset",
    )
    parser.add_argument(
        "--answer-key-path",
        default=DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH,
        help="Path to benchmark answer key",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=SETTINGS.default_top_k,
        help="Retriever top_k used during the demo run",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_DEMO_OUTPUT_PATH,
        help="JSON artifact path for the demo result",
    )
    return parser


def _first_answered_item(
    *,
    benchmark_json_path: str,
    answer_key_path: str,
) -> tuple[dict[str, Any], set[str]]:
    """Return the first benchmark item that has a gold answer."""

    items = load_retrieval_benchmark_items(benchmark_json_path)
    answer_key = load_retrieval_answer_key(answer_key_path)

    for item in items:
        item_id = int(item["id"])
        if item_id in answer_key:
            logger.info(
                "Grila selectata: id=%s, gold=%s",
                item_id,
                sorted(answer_key[item_id]),
            )
            return item, answer_key[item_id]

    raise RuntimeError("No benchmark item with a matching answer-key entry was found.")


def _log_hit(prefix: str, hit: RetrievalHit) -> None:
    """Log a compact retrieval hit line for terminal demo output."""

    text = " ".join((hit.text or "").split())
    if len(text) > 220:
        text = f"{text[:217]}..."
    logger.info(
        "%s score=%.4f source_file=%s section=%s chunk_id=%s text=%s",
        prefix,
        float(hit.score),
        hit.source_file or hit.source or "unknown",
        hit.section or "unknown",
        hit.chunk_id or "unknown",
        text,
    )


def _run_logged_pipeline(
    *,
    item: dict[str, Any],
    gold: set[str],
    top_k: int,
) -> dict[str, Any]:
    """Run one benchmark item while logging retrieval, rerank, LLM, and scoring."""

    from llm.llm_router import llm_ask_request
    from rag.retrieval.retriever import retrieve_top_similar

    item_id = int(item["id"])
    prompt = _build_grila_prompt(item)
    option_queries = _build_option_queries(item)
    candidate_k = max(top_k * RETRIEVAL_POOL_MULTIPLIER, top_k + RETRIEVAL_POOL_EXTRA)
    pooled_hits: list[RetrievalHit] = []

    logger.info(
        "Retrieval fan-out: %s apeluri Qdrant, candidate_k=%s",
        len(option_queries),
        candidate_k,
    )
    for index, retrieval_query in enumerate(option_queries, start=1):
        logger.info("Qdrant call %s/%s query=%s", index, len(option_queries), retrieval_query)
        retrieval_result = retrieve_top_similar(
            retrieval_query,
            top_k=candidate_k,
            filter_by=None,
            retrieval_mode=SETTINGS.retrieval_mode,
        )
        logger.info("Qdrant response %s/%s hits=%s", index, len(option_queries), len(retrieval_result.hits))
        for hit_index, hit in enumerate(retrieval_result.hits[:3], start=1):
            _log_hit(f"Qdrant response {index}.{hit_index}", hit)
        pooled_hits.extend(retrieval_result.hits)

    logger.info("Pool retrieval: total_hits=%s", len(pooled_hits))
    reranked_hits = _rerank_benchmark_hits(item, pooled_hits, top_k=top_k)
    logger.info("Rerank rezultat: top_%s chunks", top_k)
    for index, hit in enumerate(reranked_hits, start=1):
        _log_hit(f"Rerank top {index}", hit)

    context_block = _build_benchmark_context_block(item, reranked_hits)
    request = LLMRequest(
        system_prompt=BENCHMARK_SYSTEM_PROMPT,
        user_message=prompt,
        context_block=context_block,
        temperature=0.0,
        provider=SETTINGS.llm_provider,
    )
    logger.info("LLM call: provider=%s, context_chunks=%s", SETTINGS.llm_provider, len(reranked_hits))
    model_response = llm_ask_request(request).content.strip()
    logger.info("LLM response raw:\n%s", model_response)

    predicted = _extract_benchmark_prediction(item, model_response)
    rejection_reason = _benchmark_rejection_reason(item, model_response)
    score = _score_prediction(predicted, gold)
    logger.info(
        "Scoring: gold=%s predicted=%s exact_match=%s precision=%s recall=%s f1=%s rejection_reason=%s",
        sorted(gold),
        sorted(predicted),
        score["exact_match"],
        _percent(score["precision"]),
        _percent(score["recall"]),
        _percent(score["f1"]),
        rejection_reason,
    )

    return {
        "benchmark_json_path": DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
        "answer_key_path": DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH,
        "dataset_total_count": 1,
        "evaluated_count": 1,
        "guardrail_enabled_during_benchmark": False,
        "missing_answer_ids": [],
        "answer_key_coverage": 1.0,
        "supports_multiple_correct_answers": True,
        "global_score": round((float(score["f1"]) + int(bool(score["exact_match"]))) / 2, 4),
        "global_exact_match_rate": 1.0 if score["exact_match"] else 0.0,
        "aggregate": {
            "exact_match_rate": 1.0 if score["exact_match"] else 0.0,
            "macro_precision": score["precision"],
            "macro_recall": score["recall"],
            "macro_f1": score["f1"],
            "micro_precision": score["precision"],
            "micro_recall": score["recall"],
            "micro_f1": score["f1"],
        },
        "rows": [
            {
                "id": item_id,
                "query": item["intrebare"],
                "gold_answers": sorted(gold),
                "predicted_answers": sorted(predicted),
                "single_answer_retry_used": False,
                "raw_response": model_response,
                "rejection_reason": rejection_reason,
                "retrieved_chunks": _serialize_retrieved_chunks(reranked_hits),
                **score,
            }
        ],
    }


def run_demo(
    *,
    benchmark_json_path: str = DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
    answer_key_path: str = DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH,
    top_k: int = SETTINGS.default_top_k,
    output: str = DEFAULT_DEMO_OUTPUT_PATH,
) -> dict[str, Any]:
    """Run the first-grid benchmark demo and write its JSON artifact."""

    first_item, gold = _first_answered_item(
        benchmark_json_path=benchmark_json_path,
        answer_key_path=answer_key_path,
    )
    result = _run_logged_pipeline(
        item=first_item,
        gold=gold,
        top_k=top_k,
    )

    payload = serialize_to_json_compatible(result)
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    first_row = rows[0] if rows else {}
    aggregate = payload.get("aggregate", {}) if isinstance(payload, dict) else {}
    logger.info(
        "Benchmark demo aggregate: exact_match_rate=%s, macro_f1=%s, micro_f1=%s, global_score=%s",
        _percent(aggregate.get("exact_match_rate")),
        _percent(aggregate.get("macro_f1")),
        _percent(aggregate.get("micro_f1")),
        _percent(payload.get("global_score") if isinstance(payload, dict) else None),
    )
    logger.info("Artifact stage: benchmark demo written to %s", output_path)
    return payload


def main() -> None:
    setup_logging()
    _quiet_transport_logs()
    new_correlation_id()
    parser = _build_parser()
    args = parser.parse_args()

    ensure_startup_valid()
    run_demo(
        benchmark_json_path=args.benchmark_json_path,
        answer_key_path=args.answer_key_path,
        top_k=args.top_k,
        output=args.output,
    )


if __name__ == "__main__":
    main()
