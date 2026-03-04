from __future__ import annotations

import re
from itertools import permutations, product

from knowledge.graph.ids import build_entity_id
from models.contracts import MedicalEntity, MedicalRelation, PdfStructuredChunk

_TRIGGERS = {
    "drug_treats_disease": [r"\btrateaza\b", r"\btratament(?:ul)?\b", r"\brecomandat[ae]?\b"],
    "condition_causes_symptom": [r"\bcauzeaza\b", r"\bprovoaca\b", r"\bdetermina\b", r"\bduce la\b"],
    "disease_differs_from_disease": [
        r"\bdifer\w*\b",
        r"\bdiferential\b",
        r"\bvs\b",
        r"\bversus\b",
        r"\bspre deosebire de\b",
    ],
}


def _has_trigger(text: str, patterns: list[str]) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def _dedup_relations(relations: list[MedicalRelation]) -> list[MedicalRelation]:
    by_key: dict[tuple[str, str, str, str, int, str], MedicalRelation] = {}
    for relation in relations:
        key = (
            relation.predicate,
            relation.source_entity_id,
            relation.target_entity_id,
            relation.source_file,
            relation.page,
            relation.chunk_id,
        )
        current = by_key.get(key)
        if current is None or relation.confidence > current.confidence:
            by_key[key] = relation
    return list(by_key.values())


def extract_relations_from_chunk(
    chunk: PdfStructuredChunk,
    entities: list[MedicalEntity],
    *,
    min_confidence: float = 0.7,
) -> list[MedicalRelation]:
    diseases = [entity for entity in entities if entity.entity_type == "disease"]
    symptoms = [entity for entity in entities if entity.entity_type == "symptom"]
    drugs = [entity for entity in entities if entity.entity_type == "drug"]

    relations: list[MedicalRelation] = []
    text = chunk.text.lower()

    for disease, symptom in product(diseases, symptoms):
        confidence = min(0.95, (disease.confidence + symptom.confidence) / 2)
        if confidence < min_confidence:
            continue
        relations.append(
            MedicalRelation(
                predicate="disease_has_symptom",
                source_entity_id=build_entity_id(disease.entity_type, disease.canonical_form),
                source_entity_type=disease.entity_type,
                source_canonical_form=disease.canonical_form,
                target_entity_id=build_entity_id(symptom.entity_type, symptom.canonical_form),
                target_entity_type=symptom.entity_type,
                target_canonical_form=symptom.canonical_form,
                confidence=confidence,
                source_file=chunk.source_file,
                page=chunk.page,
                chunk_id=chunk.chunk_id,
                chapter=chunk.chapter,
                section=chunk.section,
                evidence_text=chunk.text,
            )
        )

    if _has_trigger(text, _TRIGGERS["drug_treats_disease"]):
        for drug, disease in product(drugs, diseases):
            confidence = min(0.95, (drug.confidence + disease.confidence) / 2 + 0.08)
            if confidence < min_confidence:
                continue
            relations.append(
                MedicalRelation(
                    predicate="drug_treats_disease",
                    source_entity_id=build_entity_id(drug.entity_type, drug.canonical_form),
                    source_entity_type=drug.entity_type,
                    source_canonical_form=drug.canonical_form,
                    target_entity_id=build_entity_id(disease.entity_type, disease.canonical_form),
                    target_entity_type=disease.entity_type,
                    target_canonical_form=disease.canonical_form,
                    confidence=confidence,
                    source_file=chunk.source_file,
                    page=chunk.page,
                    chunk_id=chunk.chunk_id,
                    chapter=chunk.chapter,
                    section=chunk.section,
                    evidence_text=chunk.text,
                )
            )

    if _has_trigger(text, _TRIGGERS["condition_causes_symptom"]):
        for condition, symptom in product(diseases, symptoms):
            confidence = min(0.95, (condition.confidence + symptom.confidence) / 2 + 0.06)
            if confidence < min_confidence:
                continue
            relations.append(
                MedicalRelation(
                    predicate="condition_causes_symptom",
                    source_entity_id=build_entity_id(condition.entity_type, condition.canonical_form),
                    source_entity_type=condition.entity_type,
                    source_canonical_form=condition.canonical_form,
                    target_entity_id=build_entity_id(symptom.entity_type, symptom.canonical_form),
                    target_entity_type=symptom.entity_type,
                    target_canonical_form=symptom.canonical_form,
                    confidence=confidence,
                    source_file=chunk.source_file,
                    page=chunk.page,
                    chunk_id=chunk.chunk_id,
                    chapter=chunk.chapter,
                    section=chunk.section,
                    evidence_text=chunk.text,
                )
            )

    if len(diseases) >= 2 and _has_trigger(text, _TRIGGERS["disease_differs_from_disease"]):
        for left, right in permutations(diseases, 2):
            if left.canonical_form == right.canonical_form:
                continue
            confidence = min(0.95, (left.confidence + right.confidence) / 2 + 0.05)
            if confidence < min_confidence:
                continue
            relations.append(
                MedicalRelation(
                    predicate="disease_differs_from_disease",
                    source_entity_id=build_entity_id(left.entity_type, left.canonical_form),
                    source_entity_type=left.entity_type,
                    source_canonical_form=left.canonical_form,
                    target_entity_id=build_entity_id(right.entity_type, right.canonical_form),
                    target_entity_type=right.entity_type,
                    target_canonical_form=right.canonical_form,
                    confidence=confidence,
                    source_file=chunk.source_file,
                    page=chunk.page,
                    chunk_id=chunk.chunk_id,
                    chapter=chunk.chapter,
                    section=chunk.section,
                    evidence_text=chunk.text,
                )
            )

    return _dedup_relations(relations)
