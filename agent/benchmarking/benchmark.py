"""Benchmark utilities for Romanian medical multiple-choice evaluation."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from statistics import mean
from typing import Any

from agent.evaluation.evaluator import evaluate_response
from config.eval_config import EVAL_CONFIG
from config.settings import SETTINGS
from models import EvaluatorResult, GuardrailResult, LLMRequest, RetrievalHit

DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH = "data/dataset/primele_10_grile_pag2_curatate.json"
DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH = "data/dataset/primele_10_grile_pag2_answer_key.txt"
DEFAULT_BENCHMARK_LANGUAGE = "ro"
DEFAULT_BENCHMARK_TOP_K = 3
RETRIEVAL_POOL_MULTIPLIER = 3
RETRIEVAL_POOL_EXTRA = 4
MIN_RESPONSE_ATTEMPTS = 1
REVIEW_RETRY_MESSAGE = (
    "Revizuire obligatorie: raspunsul anterior nu a fost suficient de "
    "bine sustinut de context sau de strict. Raspuns anterior: {previous_response}"
)
KEY_ORDER = "ORDER"
KEY_ASSOCIATIONS = "ASSOCIATIONS"
KEY_VARIANT = "OPTION"
KEY_FRAGMENT_ISSUE = "ISSUE_FRAGMENT"
QUESTION_PHRASE_SEQUENCE = "care este lantul temporal corect"
QUESTION_PHRASE_MAPPING = "care sunt asocierile corecte"
QUESTION_PHRASE_SCFCE_DOTTED = "s.c.f.c.e."
QUESTION_PHRASE_SCFCE_SPACED = "s c f c e"
STATUS_TRUE = "TRUE"
STATUS_FALSE = "FALSE"
REJECTION_EMPTY_RESPONSE = "empty_response"
REJECTION_FORBIDDEN_REASONING = "forbidden_reasoning"
REJECTION_MISSING_ANSWER_LETTERS = "missing_answer_letters"
REJECTION_MISSING_OR_INVALID_VARIANT = "missing_or_invalid_variant"
REJECTION_DERIVED_VALUE_VARIANT_MISMATCH = "derived_value_variant_mismatch"
REJECTION_ANSWER_VARIANT_MISMATCH = "answer_variant_mismatch"
REJECTION_MISSING_OR_INVALID_FRAGMENT = "missing_or_invalid_fragment"
REJECTION_ANSWER_FRAGMENT_MISMATCH = "answer_fragment_mismatch"
REJECTION_SINGLE_ANSWER_COUNT_MISMATCH = "single_answer_count_mismatch"
REJECTION_SINGLE_ANSWER_STATUS_MISMATCH = "single_answer_status_mismatch"
REJECTION_ALL_OPTIONS_SELECTED = "all_options_selected"
REJECTION_NO_DERIVED_ANSWERS = "no_derived_answers"
REJECTION_STATUS_ANSWER_MISMATCH = "status_answer_mismatch"
BENCHMARK_SYSTEM_PROMPT = """
You are solving Romanian medical multiple-choice benchmark items using ONLY the retrieved context.

Rules:
- Answer in Romanian.
- Be conservative: mark an option as correct only if the context supports it clearly.
- `ANSWER` must contain only option letters, never explanations and never option text.
- Derive `ANSWER` mechanically from the structured fields you output; do not add extra letters after the status check.
- For R.I. and u.a.s.c.c.e., verify each option independently before selecting letters.
- For R.I. and u.a.s.c.c.e., use `INSUFICIENT` by default when the context does not directly confirm an option.
- Never mark an option `TRUE` for R.I. / u.a.s.c.c.e. unless the support is explicit in the retrieved context.
- For R.I., final answer letters are the options marked `TRUE`.
- For u.a.s.c.c.e., final answer letters are the options marked `FALSE`.
- For R.I. and u.a.s.c.c.e., never include options marked `INSUFICIENT` in `ANSWER`.
- If all five options would be selected, re-check the statuses; this is usually an over-selection error.
- For F.d.u. and F.d.d. sequence/association items, derive the correct order or mapping from context first, then compare all A-E variants and choose the single best option.
- For u.f.d.f.d., u.i.d.f.d., u.f.c.d., c.d.d., and c.e., determine the single required letter exactly from context.
- For single-answer items, `ANSWER` must contain exactly one letter. If several options look plausible, choose the one that matches the question wording most directly.
- Do not use popularity, intuition, or outside medical knowledge when context is weak.
- Follow the exact structured output format requested in the user prompt.
- Never use unsupported claims like "cunostinte generale", "in general", or facts outside context.
""".strip()

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
    r"\b(?:u\.?i\.?d\.?f\.?d\.?|u\.?f\.?d\.?f\.?d\.?|u\.?f\.?c\.?d\.?|u\.?c\.?e\.?|f\.?d\.?u\.?|f\.?d\.?d\.?|c\.?d\.?d\.?|c\.?e\.?)\b",
    flags=re.IGNORECASE,
)
_MULTI_ANSWER_TYPE_RE = re.compile(
    r"\b(?:r\.?i\.?|u\.?a\.?s\.?c\.?c\.?e\.?)\b",
    flags=re.IGNORECASE,
)
_SEQUENCE_OPTION_RE = re.compile(r"^[a-e](?:\s*-\s*[a-e]){2,}$", flags=re.IGNORECASE)
_MAPPING_OPTION_RE = re.compile(
    r"^[a-z0-9]+\s*-\s*[a-z0-9]+(?:\s*,\s*[a-z0-9]+\s*-\s*[a-z0-9]+){1,}$",
    flags=re.IGNORECASE,
)
_TOKEN_RE = re.compile(r"\w+", flags=re.UNICODE)
_FORBIDDEN_REASONING_RE = re.compile(
    r"\b(?:cunostinte generale|cunoștințe generale|in general|în general|outside context)\b",
    flags=re.IGNORECASE,
)
_SINGLE_ANSWER_PHRASES = (
    "una falsa dintre cele date",
    "una adevarata dintre cele date",
    "una corecta dintre cele date",
    "una incorecta dintre cele date",
    "fals dintre cele date",
    "care dintre cele date",
    "care este exceptia",
    "care este exceptiile",
)


def _extract_answer_segment(value: str) -> str:
    """Extract the candidate answer line from raw model output."""

    marker_match = _ANSWER_SEGMENT_RE.search(value)
    if marker_match:
        return marker_match.group(1)

    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _normalize_romanian_text(value: str) -> str:
    """Normalize common Romanian diacritics and lowercase text."""

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
    """Parse answer letters (A-E) from response text."""

    answer_segment = _extract_answer_segment(value)
    normalized = answer_segment.upper().strip()
    if not normalized:
        return set()

    tokens: set[str] = set()
    for raw_token in re.split(r"[\s,;/|]+", normalized):
        token = raw_token.strip("().:-")
        if token in _CHOICE_LETTERS:
            tokens.add(token)
    if tokens:
        return tokens

    # Fallback for malformed output like "E-C-A-B-D" where the chosen option
    # letter is emitted together with option content.
    leading_match = re.match(r"^\s*([A-E])(?:\b|[-:])", normalized)
    if leading_match:
        return {leading_match.group(1)}
    return set()


def _normalize_answer_letters(raw: Any) -> set[str]:
    """Normalize answer representations into a set of option letters."""

    if isinstance(raw, str):
        return _extract_option_letters(raw)
    if isinstance(raw, (list, tuple, set)):
        normalized: set[str] = set()
        for item in raw:
            normalized.update(_extract_option_letters(str(item)))
        return normalized
    return set()


def _safe_int(value: Any) -> int | None:
    """Parse int while tolerating invalid values."""

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_question_text(raw: dict[str, Any]) -> str:
    """Extract question text from supported input key aliases."""

    for key in _QUESTION_KEYS:
        value = str(raw.get(key, "")).strip()
        if value:
            return value
    return ""


def _extract_choices(raw: dict[str, Any]) -> dict[str, str]:
    """Extract A-E options from flat or nested dataset formats."""

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
    """Extract gold answer letters from one answer-key entry."""

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
    """Heuristically decide whether a question expects exactly one letter."""

    normalized = _normalize_romanian_text(question)
    if _MULTI_ANSWER_TYPE_RE.search(normalized):
        return False
    if _SINGLE_ANSWER_TYPE_RE.search(normalized):
        return True
    if "care este lantul temporal corect" in normalized:
        return True
    if "care sunt asocierile corecte" in normalized:
        return True
    return any(phrase in normalized for phrase in _SINGLE_ANSWER_PHRASES)


def _choice_pattern_implies_single_answer(choices: dict[str, str]) -> bool:
    """Detect single-answer patterns from option formatting."""

    values = [value.strip() for value in choices.values() if value and value.strip()]
    if not values:
        return False
    if all(_SEQUENCE_OPTION_RE.fullmatch(value) for value in values):
        return True
    if all(_MAPPING_OPTION_RE.fullmatch(value) for value in values):
        return True
    return False


def _benchmark_requires_single_answer(item: dict[str, Any]) -> bool:
    """Decide if benchmark item requires exactly one answer letter."""

    question = str(item.get("intrebare", ""))
    choices = item.get("choices", {})
    normalized_question = _normalize_romanian_text(question)
    if "s.c.f.c.e." in normalized_question or "s c f c e" in normalized_question:
        return True
    if isinstance(choices, dict) and _choice_pattern_implies_single_answer(choices):
        return True
    return _requires_single_answer(question)


def _tokenize(value: str) -> set[str]:
    """Tokenize normalized text into alphanumeric tokens."""

    return {
        token.lower()
        for token in _TOKEN_RE.findall(_normalize_romanian_text(value))
        if len(token) >= 2
    }


def _compact_pattern(value: str) -> str:
    """Build punctuation-free normalized token stream for exact pattern comparison."""

    return re.sub(r"[^a-z0-9]+", "", _normalize_romanian_text(value))


def _match_derived_value_to_option(
    item: dict[str, Any],
    derived_value: str,
) -> str | None:
    """Match derived order/mapping text to one of the option letters."""

    compact_derived = _compact_pattern(derived_value)
    if not compact_derived or compact_derived == "insuficient":
        return None
    for letter, option_value in item["choices"].items():
        if _compact_pattern(option_value) == compact_derived:
            return letter
    return None


def _build_option_queries(item: dict[str, Any]) -> list[str]:
    """Build query pool containing base question and per-option probes."""

    question = item["intrebare"]
    queries = [question]
    for letter, value in item["choices"].items():
        cleaned = value.strip()
        if not cleaned:
            continue
        queries.append(f"{question}\nOptiunea {letter}: {cleaned}")
    return queries


def _benchmark_hit_relevance(item: dict[str, Any], hit: RetrievalHit) -> float:
    """Score benchmark retrieval hits using query and option overlap signals."""

    question_tokens = _tokenize(item["intrebare"])
    hit_text = f"{hit.title} {hit.text} {hit.section or ''}"
    hit_tokens = _tokenize(hit_text)
    if not question_tokens or not hit_tokens:
        return hit.score

    overlap = len(question_tokens.intersection(hit_tokens)) / max(len(question_tokens), 1)
    option_bonus = 0.0
    compact_hit = _compact_pattern(hit_text)
    for value in item["choices"].values():
        compact_option = _compact_pattern(value)
        if compact_option and compact_option in compact_hit:
            option_bonus = max(option_bonus, 1.0)

        option_tokens = _tokenize(value)
        if not option_tokens:
            continue
        option_overlap = len(option_tokens.intersection(hit_tokens)) / max(len(option_tokens), 1)
        option_bonus = max(option_bonus, option_overlap)
    if _benchmark_requires_single_answer(item) and _choice_pattern_implies_single_answer(
        item["choices"]
    ):
        return (hit.score * 0.45) + (overlap * 0.2) + (option_bonus * 0.35)
    return (hit.score * 0.65) + (overlap * 0.2) + (option_bonus * 0.15)


def _rerank_benchmark_hits(
    item: dict[str, Any],
    hits: list[RetrievalHit],
    *,
    top_k: int,
) -> list[RetrievalHit]:
    """Rerank and deduplicate retrieval hits, preserving top-k high-signal chunks."""

    weighted = sorted(
        ((_benchmark_hit_relevance(item, hit), hit) for hit in hits),
        key=lambda pair: pair[0],
        reverse=True,
    )
    deduped: list[RetrievalHit] = []
    seen: set[tuple[str | None, int | None, str | None, str]] = set()
    for _score, hit in weighted:
        key = (hit.source_file, hit.page, hit.chunk_id, hit.text)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hit)
        if len(deduped) >= top_k:
            break
    return deduped


def _build_benchmark_context_block(item: dict[str, Any], hits: list[RetrievalHit]) -> str:
    """Render benchmark context block from retrieved chunks."""

    lines = ["Context benchmark relevant:"]
    for index, hit in enumerate(hits, start=1):
        source_file = hit.source_file or hit.source or "unknown"
        section = hit.section or "unknown"
        page = hit.page if hit.page is not None else -1
        lines.append(
            f"- [{index}] source_file={source_file}; page={page}; section={section}; "
            f"text={hit.text}"
        )
    return "\n".join(lines)


def load_retrieval_benchmark_queries(
    json_path: str = DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
) -> list[str]:
    """Load unique benchmark probe queries from dataset JSON."""

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
    """Load benchmark items normalized to id/question/choices structure."""

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
    """Load answer key from .txt or .json formats."""

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
    """Build strict benchmark prompt for one multiple-choice item."""

    choices = item["choices"]
    question_text = item["intrebare"]
    normalized_question = _normalize_romanian_text(question_text)
    is_single_answer = _benchmark_requires_single_answer(item)
    response_rule = (
        "ANSWER: <one letter from A-E>."
        if is_single_answer
        else "ANSWER: <one or more letters from A-E, comma-separated, in alphabetical order>."
    )
    fdu_hint = ""
    reasoning_rule = (
        "Mai intai evalueaza fiecare optiune A-E independent fata de context. "
        "Foloseste format structurat cu status pentru fiecare optiune. "
        "Marcheaza TRUE doar daca suportul este explicit; altfel foloseste FALSE sau INSUFICIENT. "
        "Dupa ce ai stabilit STATUS_A-E, construieste ANSWER strict din statusuri, fara litere suplimentare."
    )
    output_template = (
        "STATUS_A: TRUE/FALSE/INSUFFICIENT\n"
        "STATUS_B: TRUE/FALSE/INSUFFICIENT\n"
        "STATUS_C: TRUE/FALSE/INSUFFICIENT\n"
        "STATUS_D: TRUE/FALSE/INSUFFICIENT\n"
        "STATUS_E: TRUE/FALSE/INSUFFICIENT\n"
        "ANSWER: <final letters>"
    )
    if re.search(r"\bf\.?d\.?u\.?\b", normalized_question):
        fdu_hint = (
            "\nPentru F.d.u., raspunsul este varianta corecta unica (A-E), "
            "nu literele din interiorul variantei."
        )
    if re.search(r"\bf\.?d\.?d\.?\b", normalized_question):
        fdu_hint += (
            "\nPentru F.d.d., raspunsul este tot varianta corecta unica (A-E), "
            "aleasa dintre variantele date."
        )
    if re.search(r"\bc\.?d\.?d\.?\b", normalized_question):
        fdu_hint += (
            "\nPentru C.d.d., raspunsul este litera unica ceruta de intrebare "
            "(care dintre cele date / care NU face parte dintre cele date)."
        )
    if (
        "care este lantul temporal corect" in normalized_question
        or "inlantuirea temporala cauzala corecta" in normalized_question
    ):
        reasoning_rule = "Reconstruieste mai intai ordinea corecta a etapelor din context, apoi compara explicit cu variantele A-E si alege o singura varianta."
        output_template = (
            "ORDER: <ex. e-c-a-b-d sau INSUFICIENT>\n"
            "OPTION: <o singura litera A-E>\n"
            "ANSWER: <aceeasi litera>"
        )
    elif "care sunt asocierile corecte" in normalized_question:
        reasoning_rule = "Reconstruieste mai intai asocierile corecte din context, apoi compara explicit cu variantele A-E si alege varianta care se potriveste complet."
        output_template = (
            "ASSOCIATIONS: <ex. a-2, b-1, c-3 sau INSUFICIENT>\n"
            "OPTION: <o singura litera A-E>\n"
            "ANSWER: <aceeasi litera>"
        )
    elif "s.c.f.c.e." in normalized_question or "s c f c e" in normalized_question:
        reasoning_rule = "Construieste fraza completa in ordinea fragmentelor si identifica exact fragmentul fals sau exceptia ceruta."
        output_template = (
            "FRAZA: <fraza rezultata sau INSUFICIENT>\n"
            "ISSUE_FRAGMENT: <o singura litera A-E>\n"
            "ANSWER: <aceeasi litera>"
        )
    elif _is_uascce_question(normalized_question):
        reasoning_rule = (
            "Evalueaza fiecare optiune A-E independent fata de context si marcheaza TRUE numai cand suportul este explicit. "
            "u.a.s.c.c.e. cere literele variantelor FALSE/INCORECTE. "
            "Pentru u.a.s.c.c.e., intrebarea cere variantele FALSE/INCORECTE. "
            "In ANSWER include DOAR literele variantelor marcate FALSE. "
            "Nu include niciodata variante marcate TRUE sau INSUFICIENT. "
            "Daca o varianta este doar nesustinuta de context, marcheaz-o INSUFFICIENT si NU o include in ANSWER. "
            "Daca ANSWER ar contine A,B,C,D,E, re-evalueaza: de obicei ai confundat FALSE cu INSUFFICIENT."
        )
        output_template = (
            "STATUS_A: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_B: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_C: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_D: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_E: TRUE/FALSE/INSUFFICIENT\n"
            "ANSWER: <doar literele variantelor FALSE/INCORECTE, separate prin virgula, in ordine alfabetica>"
        )
    elif is_single_answer and _is_exception_single_question(normalized_question):
        reasoning_rule = (
            "Aceasta este o intrebare de exceptie/fals/incorect. "
            "Verifica toate variantele A-E si identifica exact varianta FALSE/INCORECTA ceruta. "
            "ANSWER trebuie sa fie exact o singura litera, iar litera aleasa trebuie sa aiba status FALSE."
        )
        output_template = (
            "STATUS_A: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_B: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_C: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_D: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_E: TRUE/FALSE/INSUFFICIENT\n"
            "ANSWER: <o singura litera, varianta FALSE/EXCEPTIA>"
        )
    elif is_single_answer:
        reasoning_rule = (
            "Verifica toate variantele A-E si identifica exact varianta ceruta de tipul intrebarii. "
            "Foloseste format structurat si marcheaza variantele nesustinute ca INSUFICIENT. "
            "ANSWER trebuie sa fie exact o singura litera, chiar daca mai multe variante sunt TRUE/FALSE/INSUFFICIENT."
        )
        output_template = (
            "STATUS_A: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_B: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_C: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_D: TRUE/FALSE/INSUFFICIENT\n"
            "STATUS_E: TRUE/FALSE/INSUFFICIENT\n"
            "ANSWER: <o singura litera>"
        )
    return f"""
Rezolva aceasta grila medicala pe baza contextului disponibil.
Raspunde strict in formatul:
{response_rule}
Nu repeta textul variantei, returneaza doar litera(ele) finala(e).{fdu_hint}
Metoda obligatorie: {reasoning_rule}
Regula de prudenta: daca suportul contextual pentru o optiune nu este explicit, nu o marca TRUE.
Regula anti-supraselectie: nu include in ANSWER litere doar pentru ca sunt nesigure; INSUFFICIENT nu este raspuns.
Regula de format: ultima linie trebuie sa fie exact `ANSWER: ` urmata doar de litera/literele finale.
Format obligatoriu exact:
{output_template}

ID: {item['id']}
Intrebare: {question_text}
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
- Return all and only TRUE/correct letters.
- Do not return INSUFFICIENT letters.

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
- Usually this is the single FALSE/incorrect statement.

u.a.s.c.c.e. (una sau unele sunt corecte)
- One or more statements may be correct.
- In this benchmark, return the FALSE/incorrect letters.
- Never return TRUE letters.
- Never return INSUFFICIENT letters.

f.d.u. (fals dintre urmatoarele)
- In acest benchmark se alege varianta corecta unica (A-E).
- Return a single letter.

f.d.d. (fals dintre datele)
- In acest benchmark se alege varianta corecta unica (A-E).
- Return a single letter.

c.d.d. (care dintre datele)
- Intrebarea cere o singura litera A-E.
- Return a single letter.

s.c.f.c.e. (se completeaza fraza corect enuntata)
- The fragments form a sentence.
- Determine which fragment makes the sentence incorrect or correct depending on the question type.
"""


def _build_single_answer_repair_prompt(
    *,
    original_prompt: str,
    previous_response: str,
) -> str:
    """Build corrective prompt enforcing one-letter answer format."""

    return (
        f"{original_prompt}\n\n"
        "Corectie obligatorie de format: aceasta intrebare cere EXACT un singur raspuns.\n"
        f"Raspunsul tau anterior a fost: {previous_response}\n"
        "Returneaza acum STRICT in format structurat valid si cu ANSWER: <o singura litera din A-E>."
    )


def _is_sequence_question(normalized_question: str) -> bool:
    """Return whether question requests a temporal-order answer."""

    return QUESTION_PHRASE_SEQUENCE in normalized_question


def _is_mapping_question(normalized_question: str) -> bool:
    """Return whether question requests association mapping."""

    return QUESTION_PHRASE_MAPPING in normalized_question


def _is_scfce_question(normalized_question: str) -> bool:
    """Return whether question is sentence-fragment completion type."""

    return (
        QUESTION_PHRASE_SCFCE_DOTTED in normalized_question
        or QUESTION_PHRASE_SCFCE_SPACED in normalized_question
    )


def _is_uascce_question(normalized_question: str) -> bool:
    """Return whether question is u.a.s.c.c.e. multi-answer type."""

    compact = re.sub(r"[^a-z]+", "", normalized_question)
    return "uascce" in compact


def _is_exception_single_question(normalized_question: str) -> bool:
    """Return whether a single-answer question asks for the false/exception option."""

    compact = re.sub(r"[^a-z]+", "", normalized_question)
    return (
        bool(re.search(r"\bc\.?e\.?\b", normalized_question))
        or "uce" in compact
        or "uidfd" in compact
        or "ufdfd" in compact
        or "exceptia" in normalized_question
        or "falsa" in normalized_question
        or "fals" in normalized_question
        or "incorecta" in normalized_question
    )


def _extract_option_statuses(response: str) -> dict[str, str]:
    """Extract STATUS_A..E fields from response, with Romanian fallback."""

    statuses: dict[str, str] = {}
    for letter in _CHOICE_LETTERS:
        status = _extract_named_line(response, f"STATUS_{letter}").upper().strip(" .")
        if not status:
            status = _extract_named_line(response, f"STATUT_{letter}").upper().strip(" .")
        status = status.replace("Ă", "A").replace("Â", "A")
        if status in {"TRUE", "ADEVARAT"}:
            status = STATUS_TRUE
        elif status in {"FALSE", "FALS"}:
            status = STATUS_FALSE
        elif status in {"INSUFFICIENT", "INSUFICIENT"}:
            status = "INSUFFICIENT"
        if status:
            statuses[letter] = status
    return statuses


def _derive_answers_from_statuses(
    *,
    normalized_question: str,
    statuses: dict[str, str],
) -> set[str]:
    """Derive predicted letters from per-option statuses."""

    if _is_uascce_question(normalized_question):
        return {letter for letter, status in statuses.items() if status == STATUS_FALSE}
    return {letter for letter, status in statuses.items() if status == STATUS_TRUE}


def _benchmark_rejection_reason(item: dict[str, Any], response: str) -> str | None:
    """Return structured rejection reason when response is invalid for benchmark policy."""

    if not response.strip():
        return REJECTION_EMPTY_RESPONSE
    if _FORBIDDEN_REASONING_RE.search(response):
        return REJECTION_FORBIDDEN_REASONING

    predicted = _extract_option_letters(response)
    if not predicted:
        return REJECTION_MISSING_ANSWER_LETTERS

    normalized_question = _normalize_romanian_text(item["intrebare"])
    is_sequence = _is_sequence_question(normalized_question)
    is_mapping = _is_mapping_question(normalized_question)
    if is_sequence or is_mapping:
        derived_key = KEY_ORDER if is_sequence else KEY_ASSOCIATIONS
        derived_value = _extract_named_line(response, derived_key)
        if not derived_value:
            fallback_key = "ORDINE" if is_sequence else "ASOCIERI"
            derived_value = _extract_named_line(response, fallback_key)
        variant = _extract_named_line(response, KEY_VARIANT).upper().strip(" .")
        if not variant:
            variant = _extract_named_line(response, "VARIANTA").upper().strip(" .")
        if len(variant) != 1 or variant not in _CHOICE_LETTERS:
            return REJECTION_MISSING_OR_INVALID_VARIANT
        matched_letter = _match_derived_value_to_option(item, derived_value)
        if matched_letter is not None and matched_letter != variant:
            return REJECTION_DERIVED_VALUE_VARIANT_MISMATCH
        if predicted != {variant}:
            return REJECTION_ANSWER_VARIANT_MISMATCH
        return None

    if _is_scfce_question(normalized_question):
        fragment = _extract_named_line(response, KEY_FRAGMENT_ISSUE).upper().strip(" .")
        if not fragment:
            fragment = _extract_named_line(response, "FRAGMENT_PROBLEMA").upper().strip(" .")
        if len(fragment) != 1 or fragment not in _CHOICE_LETTERS:
            return REJECTION_MISSING_OR_INVALID_FRAGMENT
        if predicted != {fragment}:
            return REJECTION_ANSWER_FRAGMENT_MISMATCH
        return None

    statuses = _extract_option_statuses(response)
    if not statuses:
        return None

    if _benchmark_requires_single_answer(item):
        if len(predicted) != 1:
            return REJECTION_SINGLE_ANSWER_COUNT_MISMATCH
        chosen = next(iter(predicted))
        chosen_status = statuses.get(chosen)
        if _is_exception_single_question(normalized_question):
            if chosen_status != STATUS_FALSE:
                return REJECTION_STATUS_ANSWER_MISMATCH
            return None
        if chosen_status not in {STATUS_TRUE, STATUS_FALSE}:
            return REJECTION_SINGLE_ANSWER_STATUS_MISMATCH
        return None

    derived = _derive_answers_from_statuses(
        normalized_question=normalized_question,
        statuses=statuses,
    )
    if len(derived) == len(_CHOICE_LETTERS):
        return REJECTION_ALL_OPTIONS_SELECTED
    if not derived:
        return REJECTION_NO_DERIVED_ANSWERS
    if derived != predicted:
        return REJECTION_STATUS_ANSWER_MISMATCH
    return None


def _extract_named_line(response: str, key: str) -> str:
    """Extract named key line (KEY: value) from structured model output."""

    pattern = re.compile(rf"^\s*{re.escape(key)}\s*:\s*(.+)$", flags=re.IGNORECASE | re.MULTILINE)
    match = pattern.search(response)
    if not match:
        return ""
    return match.group(1).strip()


def _score_prediction(predicted: set[str], gold: set[str]) -> dict[str, float | int | bool]:
    """Compute per-item set metrics for benchmark answers."""

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
    """Bypass guardrail during benchmark unless explicitly enabled."""

    return GuardrailResult(
        is_emergency=False,
        is_unsafe=False,
        is_valid=True,
        message=None,
        reason_code="BENCHMARK_GUARDRAIL_BYPASS",
        confidence=1.0,
    )


def _serialize_retrieved_chunks(hits: list[RetrievalHit]) -> list[dict[str, Any]]:
    """Serialize retrieval hits for benchmark report payload rows."""

    rows: list[dict[str, Any]] = []
    for hit in hits:
        rows.append(
            {
                "title": hit.title,
                "score": round(float(hit.score), 4),
                "source": hit.source,
                "source_file": hit.source_file,
                "page": hit.page,
                "section": hit.section,
                "chunk_id": hit.chunk_id,
                "text": hit.text,
            }
        )
    return rows


def run_retrieval_benchmark(
    *,
    benchmark_json_path: str = DEFAULT_RETRIEVAL_BENCHMARK_JSON_PATH,
    answer_key_path: str = DEFAULT_RETRIEVAL_BENCHMARK_ANSWER_KEY_PATH,
    top_k: int = DEFAULT_BENCHMARK_TOP_K,
    language: str = DEFAULT_BENCHMARK_LANGUAGE,
    limit: int | None = None,
    use_guardrail: bool = False,
    ask_fn: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """Run end-to-end retrieval benchmark and return aggregate/row metrics."""

    items = load_retrieval_benchmark_items(benchmark_json_path)
    answer_key = load_retrieval_answer_key(answer_key_path)
    benchmark_ask_fn: (
        Callable[[str, dict[str, Any]], tuple[str, list[RetrievalHit], str | None]] | None
    ) = None

    if ask_fn is None:
        from agent.guardrail.rules_engine import apply_guardrails
        from llm.llm_router import llm_ask_request
        from rag.retrieval.retriever import retrieve_top_similar

        def _ask_with_item(
            prompt: str, item: dict[str, Any]
        ) -> tuple[str, list[RetrievalHit], str | None]:
            guardrail = (
                apply_guardrails(prompt)
                if use_guardrail
                else _benchmark_guardrail_allow_all(prompt)
            )
            if not guardrail.is_valid:
                return guardrail.message or "", [], "guardrail_blocked"

            candidate_k = max(top_k * RETRIEVAL_POOL_MULTIPLIER, top_k + RETRIEVAL_POOL_EXTRA)
            pooled_hits: list[RetrievalHit] = []
            for retrieval_query in _build_option_queries(item):
                retrieval_result = retrieve_top_similar(
                    retrieval_query,
                    top_k=candidate_k,
                    filter_by=None,
                    retrieval_mode=SETTINGS.retrieval_mode,
                )
                pooled_hits.extend(retrieval_result.hits)
            reranked_hits = _rerank_benchmark_hits(item, pooled_hits, top_k=top_k)
            context_block = _build_benchmark_context_block(item, reranked_hits)

            max_attempts = max(EVAL_CONFIG.max_retries + 1, MIN_RESPONSE_ATTEMPTS)
            previous_response = ""
            last_rejection_reason: str | None = None
            for attempt in range(max_attempts):
                request = LLMRequest(
                    system_prompt=BENCHMARK_SYSTEM_PROMPT,
                    user_message=(
                        prompt
                        if attempt == 0
                        else (
                            f"{prompt}\n\n"
                            f"{REVIEW_RETRY_MESSAGE.format(previous_response=previous_response)}"
                        )
                    ),
                    context_block=context_block,
                    temperature=0.0,
                    provider=SETTINGS.llm_provider,
                )
                response = llm_ask_request(request).content.strip()
                previous_response = response
                rejection_reason = _benchmark_rejection_reason(item, response)
                if rejection_reason is not None:
                    last_rejection_reason = rejection_reason
                    continue
                if _extract_option_letters(response):
                    return response, reranked_hits, None
            return previous_response, reranked_hits, last_rejection_reason

        benchmark_ask_fn = _ask_with_item

    rows: list[dict[str, Any]] = []
    missing_answer_ids: list[int] = []
    total_dataset_items = len(items)

    for item in items:
        item_id = int(item["id"])
        if item_id not in answer_key:
            missing_answer_ids.append(item_id)
            continue
        prompt = _build_grila_prompt(item)
        retrieved_chunks: list[dict[str, Any]] = []
        rejection_reason: str | None = None
        if benchmark_ask_fn is not None:
            model_response, retrieved_hits, rejection_reason = benchmark_ask_fn(prompt, item)
            retrieved_chunks = _serialize_retrieved_chunks(retrieved_hits)
        else:
            model_response = ask_fn(prompt)
        predicted = _extract_option_letters(model_response)
        single_answer_retry_used = False
        if _benchmark_requires_single_answer(item) and len(predicted) != 1:
            single_answer_retry_used = True
            repair_prompt = _build_single_answer_repair_prompt(
                original_prompt=prompt,
                previous_response=model_response,
            )
            if benchmark_ask_fn is not None:
                repaired_response, retrieved_hits, rejection_reason = benchmark_ask_fn(
                    repair_prompt, item
                )
                retrieved_chunks = _serialize_retrieved_chunks(retrieved_hits)
            else:
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
                "rejection_reason": rejection_reason,
                "retrieved_chunks": retrieved_chunks,
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
    global_exact_match_rate = (
        (exact_match_count / total_dataset_items) if total_dataset_items else 0.0
    )
    macro_precision = mean(float(row["precision"]) for row in rows) if rows else 0.0
    macro_recall = mean(float(row["recall"]) for row in rows) if rows else 0.0
    macro_f1 = mean(float(row["f1"]) for row in rows) if rows else 0.0
    global_score = (
        (sum(float(row["f1"]) for row in rows) / total_dataset_items)
        if total_dataset_items
        else 0.0
    )

    return {
        "benchmark_json_path": benchmark_json_path,
        "answer_key_path": answer_key_path,
        "dataset_total_count": total_dataset_items,
        "evaluated_count": len(rows),
        "guardrail_enabled_during_benchmark": use_guardrail,
        "missing_answer_ids": missing_answer_ids,
        "answer_key_coverage": round(
            (len(rows) / total_dataset_items) if total_dataset_items else 0.0, 4
        ),
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
    """Run a deterministic evaluator smoke-check."""

    return evaluate_response(
        query="Care sunt simptomele gripei?",
        response="Gripa include febra, frisoane, tuse si dureri musculare.",
        context_lines=["Simptome frecvente: febra, tuse, dureri musculare."],
    )
