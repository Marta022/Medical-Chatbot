from __future__ import annotations

import json
import re
from pathlib import Path
from statistics import mean
from typing import Any, Callable

from agent.evaluation.evaluator import evaluate_response
from models import EvaluatorResult, GuardrailResult


DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH = "data/dataset/primele_10_grile_pag2_curatate.json"
DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH = "data/dataset/primele_10_grile_pag2_answer_key.txt"

_OPTION_RE = re.compile(r"\b([A-E])\b", flags=re.IGNORECASE)
_ANSWER_SEGMENT_RE = re.compile(
    r"(?:^|\n)\s*(?:raspuns|răspuns|answer)\s*[:\-]\s*([^\n\r]+)",
    flags=re.IGNORECASE,
)
_CHOICE_LETTERS = ("A", "B", "C", "D", "E")
_QUESTION_KEYS = ("intrebare", "question", "query", "prompt")
_ANSWER_VALUE_KEYS = (
    "answers",
    "answer",
    "raspunsuri",
    "raspuns",
    "correct_answers",
    "correct",
    "corect",
    "corecte",
    "key",
)
_SINGLE_ANSWER_TYPE_RE = re.compile(
    r"\b(?:u\.?i\.?d\.?f\.?d\.?|u\.?f\.?d\.?f\.?d\.?|u\.?f\.?c\.?d\.?|c\.?e\.?)\b",
    flags=re.IGNORECASE,
)
_SINGLE_ANSWER_PHRASES = (
    "una falsa dintre cele date",
    "una adevarata dintre cele date",
    "una corecta dintre cele date",
    "una incorecta dintre cele date",
    "care este exceptia",
    "care este exceptiile",
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


def _normalize_romanian_text(value: str) -> str:
    return (
        (value or "")
        .lower()
        .replace("ă", "a")
        .replace("â", "a")
        .replace("î", "i")
        .replace("ș", "s")
        .replace("ş", "s")
        .replace("ț", "t")
        .replace("ţ", "t")
    )


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


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_question_text(raw: dict[str, Any]) -> str:
    for key in _QUESTION_KEYS:
        value = str(raw.get(key, "")).strip()
        if value:
            return value
    return ""


def _extract_choices(raw: dict[str, Any]) -> dict[str, str]:
    direct = {letter: str(raw.get(letter, "")).strip() for letter in _CHOICE_LETTERS}
    if any(direct.values()):
        return direct

    nested = raw.get("choices", raw.get("options"))
    if isinstance(nested, dict):
        return {letter: str(nested.get(letter, "")).strip() for letter in _CHOICE_LETTERS}
    if isinstance(nested, (list, tuple)):
        values = [str(item).strip() for item in nested]
        mapped = {
            letter: (values[index] if index < len(values) else "")
            for index, letter in enumerate(_CHOICE_LETTERS)
        }
        return mapped

    return {letter: "" for letter in _CHOICE_LETTERS}


def _extract_answer_letters_from_entry(entry: dict[str, Any]) -> set[str]:
    for key in _ANSWER_VALUE_KEYS:
        if key in entry:
            parsed = _normalize_answer_letters(entry.get(key))
            if parsed:
                return parsed

    marked_letters: set[str] = set()
    for letter in _CHOICE_LETTERS:
        marker = entry.get(letter)
        if marker is True:
            marked_letters.add(letter)
        elif isinstance(marker, (int, float)) and marker == 1:
            marked_letters.add(letter)
        elif isinstance(marker, str) and marker.strip().lower() in {"1", "true", "yes", "y", "x"}:
            marked_letters.add(letter)
    return marked_letters


def _requires_single_answer(question: str) -> bool:
    normalized = _normalize_romanian_text(question)
    if _SINGLE_ANSWER_TYPE_RE.search(normalized):
        return True
    return any(phrase in normalized for phrase in _SINGLE_ANSWER_PHRASES)


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
        raw_query = _extract_question_text(item)
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
        item_id = raw.get("id", raw.get("question_id", raw.get("qid")))
        normalized_id = _safe_int(item_id)
        if normalized_id is None:
            continue
        question = _extract_question_text(raw)
        if not question:
            continue
        choices = _extract_choices(raw)
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
            nested_candidates = payload.get("answers")
            if isinstance(nested_candidates, (dict, list)):
                payload = nested_candidates
            else:
                for raw_id, raw_answers in payload.items():
                    normalized_id = _safe_int(raw_id)
                    if normalized_id is None:
                        continue
                    normalized = _normalize_answer_letters(raw_answers)
                    if not normalized:
                        continue
                    mapping[normalized_id] = normalized

        if isinstance(payload, list):
            for raw in payload:
                if not isinstance(raw, dict):
                    continue
                normalized_id = _safe_int(raw.get("id", raw.get("question_id", raw.get("qid"))))
                if normalized_id is None:
                    continue
                normalized = _extract_answer_letters_from_entry(raw)
                if not normalized:
                    continue
                mapping[normalized_id] = normalized
        elif not isinstance(payload, dict):
            raise ValueError(f"Answer key JSON must be object/list: '{answer_key_path}'.")

        if isinstance(payload, dict):
            for raw_id, raw_answers in payload.items():
                normalized_id = _safe_int(raw_id)
                if normalized_id is None:
                    continue
                normalized = _normalize_answer_letters(raw_answers)
                if not normalized:
                    continue
                mapping[normalized_id] = normalized

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
    response_rule = (
        "RASPUNS: <o singura litera din A-E>."
        if _requires_single_answer(item["intrebare"])
        else "RASPUNS: <litere separate prin virgula, in ordine alfabetica>."
    )
    return f"""
Rezolva aceasta grila medicala pe baza contextului disponibil.
Raspunde strict in formatul:
{response_rule}

ID: {item['id']}
Intrebare: {item['intrebare']}
A) {choices['A']}
B) {choices['B']}
C) {choices['C']}
D) {choices['D']}
E) {choices['E']}

You are evaluating Romanian multiple-choice medical questions.

Each question may contain a type indicator (abbreviation) that specifies how the answers must be interpreted.

Interpret them strictly as follows:

R.I. (Raspunsuri Independente)
- Each statement (A–E) is evaluated independently.
- More than one statement may be correct.
- Return all correct letters.

u.i.d.f.d. (una incorecta dintre cele date)
- Exactly one statement is incorrect.
- Return the letter of the incorrect statement.

u.f.d.f.d. (una falsa dintre cele date)
- Exactly one statement is false.
- Return the letter of the false statement.

u.f.c.d. (una corecta dintre cele date)
- Exactly one statement is true/correct.
- Return a single letter.

c.e. (care este exceptia)
- All statements are correct except one.
- Return the letter of the exception.

u.a.s.c.c.e. (una sau unele sunt corecte)
- One or more statements may be correct.
- Return all correct letters.

f.d.u. (fals dintre urmatoarele)
- Identify which statements are false.
- Return all false letters.

s.c.f.c.e. (se completeaza fraza corect enuntata)
- The fragments form a sentence.
- Determine which fragment makes the sentence incorrect or correct depending on the question type.
"""


def _build_single_answer_repair_prompt(
    *,
    original_prompt: str,
    previous_response: str,
) -> str:
    return (
        f"{original_prompt}\n\n"
        "Corectie obligatorie de format: aceasta intrebare cere EXACT un singur raspuns.\n"
        f"Raspunsul tau anterior a fost: {previous_response}\n"
        "Returneaza acum STRICT: RASPUNS: <o singura litera din A-E>, fara explicatii."
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


def _benchmark_guardrail_allow_all(_query: str) -> GuardrailResult:
    return GuardrailResult(
        is_emergency=False,
        is_unsafe=False,
        is_valid=True,
        message=None,
        reason_code="BENCHMARK_GUARDRAIL_BYPASS",
        confidence=1.0,
    )


def run_retrieval_benchmark(
    *,
    benchmark_json_path: str = DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
    answer_key_path: str = DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH,
    top_k: int = 3,
    language: str = "ro",
    limit: int | None = None,
    use_guardrail: bool = False,
    ask_fn: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    items = load_retrieval_benchmark_items(benchmark_json_path)
    answer_key = load_retrieval_answer_key(answer_key_path)

    if ask_fn is None:
        from agent.orchestrator.orchestrator import Orchestrator, OrchestratorDependencies
        from models import QueryRequest

        if use_guardrail:
            orchestrator = Orchestrator()
        else:
            benchmark_deps = OrchestratorDependencies(guardrail=_benchmark_guardrail_allow_all)
            orchestrator = Orchestrator(deps=benchmark_deps)

        def _ask(prompt: str) -> str:
            result = orchestrator.run(QueryRequest(query=prompt, top_k=top_k, language=language))
            return result.response or ""

        ask_fn = _ask

    rows: list[dict[str, Any]] = []
    missing_answer_ids: list[int] = []
    total_dataset_items = len(items)

    for item in items:
        item_id = int(item["id"])
        if item_id not in answer_key:
            missing_answer_ids.append(item_id)
            continue
        prompt = _build_grila_prompt(item)
        model_response = ask_fn(prompt)
        predicted = _extract_option_letters(model_response)
        single_answer_retry_used = False
        if _requires_single_answer(item["intrebare"]) and len(predicted) != 1:
            single_answer_retry_used = True
            repair_prompt = _build_single_answer_repair_prompt(
                original_prompt=prompt,
                previous_response=model_response,
            )
            repaired_response = ask_fn(repair_prompt)
            repaired_predicted = _extract_option_letters(repaired_response)
            if len(repaired_predicted) == 1:
                model_response = repaired_response
                predicted = repaired_predicted

        gold = answer_key[item_id]
        score = _score_prediction(predicted, gold)
        rows.append(
            {
                "id": item_id,
                "query": item["intrebare"],
                "gold_answers": sorted(gold),
                "predicted_answers": sorted(predicted),
                "single_answer_retry_used": single_answer_retry_used,
                "raw_response": model_response,
                **score,
            }
        )
        if limit is not None and limit > 0 and len(rows) >= limit:
            break

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
    exact_match_count = sum(1 for row in rows if bool(row["exact_match"]))
    exact_match_rate = (exact_match_count / len(rows)) if rows else 0.0
    global_exact_match_rate = (exact_match_count / total_dataset_items) if total_dataset_items else 0.0
    macro_precision = mean(float(row["precision"]) for row in rows) if rows else 0.0
    macro_recall = mean(float(row["recall"]) for row in rows) if rows else 0.0
    macro_f1 = mean(float(row["f1"]) for row in rows) if rows else 0.0
    global_score = (sum(float(row["f1"]) for row in rows) / total_dataset_items) if total_dataset_items else 0.0

    return {
        "benchmark_json_path": benchmark_json_path,
        "answer_key_path": answer_key_path,
        "dataset_total_count": total_dataset_items,
        "evaluated_count": len(rows),
        "guardrail_enabled_during_benchmark": use_guardrail,
        "missing_answer_ids": missing_answer_ids,
        "answer_key_coverage": round((len(rows) / total_dataset_items) if total_dataset_items else 0.0, 4),
        "supports_multiple_correct_answers": True,
        "global_score": round(global_score, 4),
        "global_exact_match_rate": round(global_exact_match_rate, 4),
        "aggregate": {
            "exact_match_rate": round(exact_match_rate, 4),
            "macro_precision": round(macro_precision, 4),
            "macro_recall": round(macro_recall, 4),
            "macro_f1": round(macro_f1, 4),
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
