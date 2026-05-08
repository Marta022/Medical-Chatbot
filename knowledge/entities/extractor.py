from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from models.contracts import MedicalEntity, PdfStructuredChunk
from models.text_normalization import normalize_for_matching

logger = logging.getLogger(__name__)

_SYMPTOM_TERMS = {
    "durere toracica",
    "dispnee",
    "tuse",
    "febra",
    "frisoane",
    "cefalee",
    "greata",
    "varsaturi",
    "palpitatii",
    "oboseala",
    "edeme",
}
_DRUG_TERMS = {
    "aspirina",
    "paracetamol",
    "ibuprofen",
    "metformin",
    "insulina",
    "atorvastatina",
}
_ANATOMY_TERMS = {
    "inima",
    "plamani",
    "stomac",
    "ficat",
    "rinichi",
    "creier",
    "artere",
    "vene",
}
_ALIASES = {
    "mi": "myocardial infarction",
    "infarct miocardic": "myocardial infarction",
    "hta": "hipertensiune arteriala",
    "bpoc": "bronhopneumopatie obstructiva cronica",
    "covid": "covid-19",
}
DEFAULT_ENTITY_MIN_CONFIDENCE = 0.65
ALIAS_DISEASE_CONFIDENCE = 0.85
DATASET_DISEASE_CONFIDENCE = 0.9
TERM_CONFIDENCE_BY_TYPE: dict[str, float] = {
    "symptom": 0.78,
    "drug": 0.8,
    "anatomy": 0.76,
}


def _normalize(text: str) -> str:
    """Normalize text for accent-insensitive and case-insensitive matching."""

    return normalize_for_matching(text)


def load_disease_terms(dataset_json_path: str) -> set[str]:
    """Load normalized disease names from dataset JSON categories."""

    source = Path(dataset_json_path)
    if not source.exists():
        logger.debug("disease_terms_file_missing", extra={"path": str(source)})
        return set()
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(
            "disease_terms_load_failed",
            extra={"path": str(source), "error": str(exc)},
        )
        return set()
    if not isinstance(data, list):
        logger.warning(
            "disease_terms_invalid_payload",
            extra={"path": str(source), "payload_type": type(data).__name__},
        )
        return set()

    terms: set[str] = set()
    for category in data:
        if not isinstance(category, dict):
            continue
        for disease in category.get("diseases", []):
            if not isinstance(disease, dict):
                continue
            name = str(disease.get("name", "")).strip()
            if name:
                terms.add(_normalize(name))
    return terms


def _find_term_mentions(text: str, terms: set[str]) -> list[tuple[str, str]]:
    """Find exact-word normalized term matches inside text."""

    normalized_text = _normalize(text)
    found: list[tuple[str, str]] = []
    for term in sorted(terms, key=len, reverse=True):
        if not term:
            continue
        pattern = rf"(?<!\w){re.escape(term)}(?!\w)"
        if re.search(pattern, normalized_text):
            found.append((term, term))
    return found


def extract_entities_from_chunk(
    chunk: PdfStructuredChunk,
    *,
    disease_terms: set[str],
    min_confidence: float = DEFAULT_ENTITY_MIN_CONFIDENCE,
) -> list[MedicalEntity]:
    """Extract deterministic medical entities from one structured chunk."""

    entities: list[MedicalEntity] = []
    normalized_text = _normalize(chunk.text)

    seen: set[tuple[str, str]] = set()

    for alias, canonical in _ALIASES.items():
        pattern = rf"(?<!\w){re.escape(alias)}(?!\w)"
        if not re.search(pattern, normalized_text):
            continue
        key = ("disease", canonical)
        if key in seen:
            continue
        seen.add(key)
        entity = MedicalEntity(
            entity_type="disease",
            mention_text=alias,
            canonical_form=canonical,
            confidence=ALIAS_DISEASE_CONFIDENCE,
            source_file=chunk.source_file,
            page=chunk.page,
            chunk_id=chunk.chunk_id,
            chapter=chunk.chapter,
            section=chunk.section,
        )
        if entity.confidence >= min_confidence:
            entities.append(entity)

    for term, mention in _find_term_mentions(chunk.text, disease_terms):
        key = ("disease", term)
        if key in seen:
            continue
        seen.add(key)
        entity = MedicalEntity(
            entity_type="disease",
            mention_text=mention,
            canonical_form=term,
            confidence=DATASET_DISEASE_CONFIDENCE,
            source_file=chunk.source_file,
            page=chunk.page,
            chunk_id=chunk.chunk_id,
            chapter=chunk.chapter,
            section=chunk.section,
        )
        if entity.confidence >= min_confidence:
            entities.append(entity)

    for entity_type, terms in [
        ("symptom", _SYMPTOM_TERMS),
        ("drug", _DRUG_TERMS),
        ("anatomy", _ANATOMY_TERMS),
    ]:
        confidence = TERM_CONFIDENCE_BY_TYPE[entity_type]
        for term, mention in _find_term_mentions(chunk.text, terms):
            key = (entity_type, term)
            if key in seen:
                continue
            seen.add(key)
            entity = MedicalEntity(
                entity_type=entity_type,
                mention_text=mention,
                canonical_form=term,
                confidence=confidence,
                source_file=chunk.source_file,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
                chapter=chunk.chapter,
                section=chunk.section,
            )
            if entity.confidence >= min_confidence:
                entities.append(entity)

    return entities


def extract_entities_from_chunks(
    chunks: list[PdfStructuredChunk],
    *,
    dataset_json_path: str,
    min_confidence: float = DEFAULT_ENTITY_MIN_CONFIDENCE,
) -> list[MedicalEntity]:
    """Extract entities across chunk list using dataset disease terminology."""

    disease_terms = load_disease_terms(dataset_json_path)
    results: list[MedicalEntity] = []
    for chunk in chunks:
        results.extend(
            extract_entities_from_chunk(
                chunk,
                disease_terms=disease_terms,
                min_confidence=min_confidence,
            )
        )
    return results
