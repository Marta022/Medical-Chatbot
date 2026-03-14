from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean
from typing import Any, Callable

from agent.evaluation.evaluator import evaluate_response
from models import EvaluatorResult


DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH = "data/dataset/primele_10_grile_pag2_curatate.json"
DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH = "data/dataset/primele_10_grile_pag2_answer_key.txt"

_OPTION_RE = re.compile(r"\b([A-E])\b", flags=re.IGNORECASE)
_ANSWER_SEGMENT_RE = re.compile(
    r"(?:^|\n)\s*(?:raspuns|răspuns|answer)\s*[:\-]\s*([^\n\r]+)",
    flags=re.IGNORECASE,
)


def _extract_answer_segment(value: str) -> str:
    marker_match = _ANSWER_SEGMENT_RE.search(value)
    if marker_match:
        return marker_match.group(1)

    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _extract_option_letters(value: str) -> set[str]:
    answer_segment = _extract_answer_segment(value)
    return {match.upper() for match in _OPTION_RE.findall(answer_segment)}


def _normalize_answer_letters(raw: Any) -> set[str]:
    if isinstance(raw, str):
        return _extract_option_letters(raw)
    if isinstance(raw, (list, tuple, set)):
        normalized: set[str] = set()
        for item in raw:
            normalized.update(_extract_option_letters(str(item)))
        return normalized
    return set()


def load_retrieval_benchmark_queries(
    json_path: str = DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
) -> list[str]:
    source = Path(json_path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Probe dataset must be a list of objects: '{json_path}'.")

    seen: set[str] = set()
    probes: list[str] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        raw_query = str(item.get("intrebare", "")).strip()
        if not raw_query or raw_query in seen:
            continue
        seen.add(raw_query)
        probes.append(raw_query)

    if not probes:
        raise ValueError(
            f"Probe dataset did not contain any valid 'intrebare' entries: '{json_path}'."
        )
    return probes


def load_retrieval_benchmark_items(
    json_path: str = DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
) -> list[dict[str, Any]]:
    source = Path(json_path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Benchmark dataset must be a list of objects: '{json_path}'.")

    items: list[dict[str, Any]] = []
    for raw in payload:
        if not isinstance(raw, dict):
            continue
        item_id = raw.get("id")
        if item_id is None:
            continue
        try:
            normalized_id = int(item_id)
        except (TypeError, ValueError):
            continue
        question = str(raw.get("intrebare", "")).strip()
        if not question:
            continue
        choices = {letter: str(raw.get(letter, "")).strip() for letter in ["A", "B", "C", "D", "E"]}
        items.append(
            {
                "id": normalized_id,
                "intrebare": question,
                "choices": choices,
            }
        )

    if not items:
        raise ValueError(f"No valid benchmark items found in '{json_path}'.")
    return items


def load_retrieval_answer_key(
    answer_key_path: str = DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH,
) -> dict[int, set[str]]:
    source = Path(answer_key_path)
    suffix = source.suffix.lower()

    if suffix == ".json":
        payload = json.loads(source.read_text(encoding="utf-8"))
        mapping: dict[int, set[str]] = {}
        if isinstance(payload, dict):
            for raw_id, raw_answers in payload.items():
                normalized = _normalize_answer_letters(raw_answers)
                if not normalized:
                    continue
                mapping[int(raw_id)] = normalized
        elif isinstance(payload, list):
            for raw in payload:
                if not isinstance(raw, dict) or "id" not in raw:
                    continue
                normalized = _normalize_answer_letters(raw.get("answers", raw.get("answer", "")))
                if not normalized:
                    continue
                mapping[int(raw["id"])] = normalized
        else:
            raise ValueError(f"Answer key JSON must be object/list: '{answer_key_path}'.")
        if not mapping:
            raise ValueError(f"No valid answer entries found in '{answer_key_path}'.")
        return mapping

    mapping: dict[int, set[str]] = {}
    for line in source.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        match = re.match(r"^(\d+)\s*[:.)-]?\s*(.+)$", stripped)
        if not match:
            continue
        item_id = int(match.group(1))
        answers = _normalize_answer_letters(match.group(2))
        if answers:
            mapping[item_id] = answers

    if not mapping:
        raise ValueError(f"No valid answer entries found in '{answer_key_path}'.")
    return mapping


def _build_grila_prompt(item: dict[str, Any]) -> str:
    choices = item["choices"]
    return (
        "Rezolva aceasta grila medicala pe baza contextului disponibil. "
        "Pot exista una sau mai multe variante corecte. "
        "Raspunde strict in formatul: RASPUNS: <litere separate prin virgula, in ordine alfabetica>.\n\n"
        f"ID: {item['id']}\n"
        f"Intrebare: {item['intrebare']}\n"
        f"A) {choices['A']}\n"
        f"B) {choices['B']}\n"
        f"C) {choices['C']}\n"
        f"D) {choices['D']}\n"
        f"E) {choices['E']}"
    )


def _score_prediction(predicted: set[str], gold: set[str]) -> dict[str, float | int | bool]:
    true_positive = len(predicted & gold)
    false_positive = len(predicted - gold)
    false_negative = len(gold - predicted)
    precision = true_positive / len(predicted) if predicted else 0.0
    recall = true_positive / len(gold) if gold else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return {
        "tp": true_positive,
        "fp": false_positive,
        "fn": false_negative,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "exact_match": predicted == gold,
    }


def run_retrieval_benchmark(
    *,
    benchmark_json_path: str = DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
    answer_key_path: str = DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH,
    top_k: int = 3,
    language: str = "ro",
    limit: int | None = None,
    ask_fn: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    items = load_retrieval_benchmark_items(benchmark_json_path)
    answer_key = load_retrieval_answer_key(answer_key_path)

    if ask_fn is None:
        from agent.orchestrator.orchestrator import Orchestrator
        from models import QueryRequest

        orchestrator = Orchestrator()

        def _ask(prompt: str) -> str:
            result = orchestrator.run(QueryRequest(query=prompt, top_k=top_k, language=language))
            return result.response or ""

        ask_fn = _ask

    rows: list[dict[str, Any]] = []
    missing_answer_ids: list[int] = []

    for item in items:
        item_id = int(item["id"])
        if item_id not in answer_key:
            missing_answer_ids.append(item_id)
            continue
        prompt = _build_grila_prompt(item)
        model_response = ask_fn(prompt)
        predicted = _extract_option_letters(model_response)
        gold = answer_key[item_id]
        score = _score_prediction(predicted, gold)
        rows.append(
            {
                "id": item_id,
                "query": item["intrebare"],
                "gold_answers": sorted(gold),
                "predicted_answers": sorted(predicted),
                "raw_response": model_response,
                **score,
            }
        )
        if limit is not None and limit > 0 and len(rows) >= limit:
            break

    if not rows:
        raise ValueError("No benchmark rows were evaluated. Check answer key coverage and limit.")

    tp = sum(int(row["tp"]) for row in rows)
    fp = sum(int(row["fp"]) for row in rows)
    fn = sum(int(row["fn"]) for row in rows)
    micro_precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    micro_recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    micro_f1 = (
        2 * micro_precision * micro_recall / (micro_precision + micro_recall)
        if (micro_precision + micro_recall) > 0
        else 0.0
    )
    exact_match_rate = sum(1 for row in rows if bool(row["exact_match"])) / len(rows)

    return {
        "benchmark_json_path": benchmark_json_path,
        "answer_key_path": answer_key_path,
        "evaluated_count": len(rows),
        "missing_answer_ids": missing_answer_ids,
        "supports_multiple_correct_answers": True,
        "aggregate": {
            "exact_match_rate": round(exact_match_rate, 4),
            "macro_precision": round(mean(float(row["precision"]) for row in rows), 4),
            "macro_recall": round(mean(float(row["recall"]) for row in rows), 4),
            "macro_f1": round(mean(float(row["f1"]) for row in rows), 4),
            "micro_precision": round(micro_precision, 4),
            "micro_recall": round(micro_recall, 4),
            "micro_f1": round(micro_f1, 4),
        },
        "rows": rows,
    }


def run_evaluation_smoke() -> EvaluatorResult:
    return evaluate_response(
        query="Care sunt simptomele gripei?",
        response="Gripa include febra, frisoane, tuse si dureri musculare.",
        context_lines=["Simptome frecvente: febra, tuse, dureri musculare."],
    )
