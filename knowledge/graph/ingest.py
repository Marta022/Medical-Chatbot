from __future__ import annotations

import logging
from typing import Any

from knowledge.entities.extractor import extract_entities_from_chunk
from knowledge.graph.client import GraphClient, get_graph_client
from knowledge.graph.ids import build_entity_id, build_source_chunk_id
from knowledge.graph.relations import extract_relations_from_chunk
from knowledge.graph.schema import ensure_graph_schema
from models.contracts import MedicalEntity, MedicalRelation, PdfStructuredChunk

logger = logging.getLogger(__name__)

_PREDICATE_TABLES = {
    "disease_has_symptom": "DISEASE_HAS_SYMPTOM",
    "drug_treats_disease": "DRUG_TREATS_DISEASE",
    "condition_causes_symptom": "CONDITION_CAUSES_SYMPTOM",
    "disease_differs_from_disease": "DISEASE_DIFFERS_FROM_DISEASE",
}


def reconcile_entities(entities: list[MedicalEntity]) -> list[MedicalEntity]:
    deduped: dict[tuple[str, str], MedicalEntity] = {}
    for entity in entities:
        key = (entity.entity_type, entity.canonical_form)
        current = deduped.get(key)
        if current is None or entity.confidence > current.confidence:
            deduped[key] = entity
    return list(deduped.values())


def reconcile_relations(relations: list[MedicalRelation]) -> list[MedicalRelation]:
    deduped: dict[tuple[str, str, str], MedicalRelation] = {}
    for relation in relations:
        key = (relation.predicate, relation.source_entity_id, relation.target_entity_id)
        current = deduped.get(key)
        if current is None or relation.confidence > current.confidence:
            deduped[key] = relation
    return list(deduped.values())


def _upsert_source_chunk(graph_client: GraphClient, chunk: PdfStructuredChunk) -> str:
    source_chunk_id = build_source_chunk_id(chunk.source_file, chunk.page, chunk.chunk_id)
    graph_client.execute(
        (
            "MERGE (c:SourceChunk {source_chunk_id: $source_chunk_id}) "
            "SET c.source_file = $source_file, "
            "c.page = $page, "
            "c.chunk_id = $chunk_id, "
            "c.chapter = $chapter, "
            "c.section = $section;"
        ),
        {
            "source_chunk_id": source_chunk_id,
            "source_file": chunk.source_file,
            "page": int(chunk.page),
            "chunk_id": chunk.chunk_id,
            "chapter": chunk.chapter,
            "section": chunk.section,
        },
    )
    return source_chunk_id


def _upsert_entity(graph_client: GraphClient, entity: MedicalEntity) -> str:
    entity_id = build_entity_id(entity.entity_type, entity.canonical_form)
    graph_client.execute(
        (
            "MERGE (e:Entity {entity_id: $entity_id}) "
            "SET e.canonical_form = $canonical_form, "
            "e.entity_type = $entity_type;"
        ),
        {
            "entity_id": entity_id,
            "canonical_form": entity.canonical_form,
            "entity_type": entity.entity_type,
        },
    )
    return entity_id


def _upsert_mention_edge(
    graph_client: GraphClient,
    *,
    entity: MedicalEntity,
    source_chunk_id: str,
) -> None:
    entity_id = build_entity_id(entity.entity_type, entity.canonical_form)
    graph_client.execute(
        (
            "MATCH (e:Entity {entity_id: $entity_id}), "
            "(c:SourceChunk {source_chunk_id: $source_chunk_id}) "
            "MERGE (e)-[r:MENTIONED_IN]->(c) "
            "SET r.mention_text = $mention_text, "
            "r.confidence = $confidence, "
            "r.source_file = $source_file, "
            "r.page = $page, "
            "r.chunk_id = $chunk_id;"
        ),
        {
            "entity_id": entity_id,
            "source_chunk_id": source_chunk_id,
            "mention_text": entity.mention_text,
            "confidence": float(entity.confidence),
            "source_file": entity.source_file,
            "page": int(entity.page),
            "chunk_id": entity.chunk_id,
        },
    )


def _upsert_relation(graph_client: GraphClient, relation: MedicalRelation) -> None:
    table = _PREDICATE_TABLES[relation.predicate]
    graph_client.execute(
        (
            "MATCH (a:Entity {entity_id: $source_entity_id}), "
            "(b:Entity {entity_id: $target_entity_id}) "
            f"MERGE (a)-[r:{table}]->(b) "
            "SET r.confidence = $confidence, "
            "r.source_file = $source_file, "
            "r.page = $page, "
            "r.chunk_id = $chunk_id;"
        ),
        {
            "source_entity_id": relation.source_entity_id,
            "target_entity_id": relation.target_entity_id,
            "confidence": float(relation.confidence),
            "source_file": relation.source_file,
            "page": int(relation.page),
            "chunk_id": relation.chunk_id,
        },
    )


def ingest_pdf_chunks_to_graph(
    chunks: list[PdfStructuredChunk],
    *,
    disease_terms: set[str],
    min_entity_confidence: float = 0.65,
    min_relation_confidence: float = 0.7,
    graph_client: GraphClient | None = None,
) -> dict[str, Any]:
    owns_client = graph_client is None
    client = graph_client or get_graph_client()

    try:
        ensure_graph_schema(client)

        all_entities: list[MedicalEntity] = []
        mention_entities: list[MedicalEntity] = []
        all_relations: list[MedicalRelation] = []
        chunk_ids: set[str] = set()

        for chunk in chunks:
            entities = extract_entities_from_chunk(
                chunk,
                disease_terms=disease_terms,
                min_confidence=min_entity_confidence,
            )
            if not entities:
                continue

            source_chunk_id = _upsert_source_chunk(client, chunk)
            chunk_ids.add(source_chunk_id)
            mention_entities.extend(entities)

            for entity in entities:
                all_entities.append(entity)
                _upsert_entity(client, entity)
                _upsert_mention_edge(client, entity=entity, source_chunk_id=source_chunk_id)

            extracted_relations = extract_relations_from_chunk(
                chunk,
                entities,
                min_confidence=min_relation_confidence,
            )
            all_relations.extend(extracted_relations)

        unique_entities = reconcile_entities(all_entities)

        unique_relations = reconcile_relations(all_relations)
        for relation in unique_relations:
            _upsert_relation(client, relation)

        return {
            "chunks": len(chunk_ids),
            "mentions": len(mention_entities),
            "entities": len(unique_entities),
            "relations": len(unique_relations),
        }
    finally:
        if owns_client:
            client.close()


def ingest_pdf_chunks_to_graph_safe(
    chunks: list[PdfStructuredChunk],
    *,
    disease_terms: set[str],
    min_entity_confidence: float = 0.65,
    min_relation_confidence: float = 0.7,
) -> dict[str, Any]:
    try:
        return ingest_pdf_chunks_to_graph(
            chunks,
            disease_terms=disease_terms,
            min_entity_confidence=min_entity_confidence,
            min_relation_confidence=min_relation_confidence,
        )
    except RuntimeError:
        logger.warning("Skipping graph ingestion because graph backend is unavailable.")
        return {"chunks": 0, "mentions": 0, "entities": 0, "relations": 0}
