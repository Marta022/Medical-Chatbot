from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

from models.contracts import MedicalEntity, PdfStructuredChunk

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


def _normalize(text: str) -> str:
    base = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in base if unicodedata.category(ch) != "Mn").strip()


def load_disease_terms(dataset_json_path: str) -> set[str]:
    source = Path(dataset_json_path)
    if not source.exists():
        return set()
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except Exception:
        return set()
    if not isinstance(data, list):
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
    min_confidence: float = 0.65,
) -> list[MedicalEntity]:
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
            confidence=0.85,
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
            confidence=0.9,
            source_file=chunk.source_file,
            page=chunk.page,
            chunk_id=chunk.chunk_id,
            chapter=chunk.chapter,
            section=chunk.section,
        )
        if entity.confidence >= min_confidence:
            entities.append(entity)

    for entity_type, terms, confidence in [
        ("symptom", _SYMPTOM_TERMS, 0.78),
        ("drug", _DRUG_TERMS, 0.8),
        ("anatomy", _ANATOMY_TERMS, 0.76),
    ]:
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
    min_confidence: float = 0.65,
) -> list[MedicalEntity]:
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
