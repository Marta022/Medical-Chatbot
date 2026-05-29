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
