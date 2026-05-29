def ingest(
    json_path: str,
    csv_path: str,
    chunking_strategy: str = DEFAULT_CHUNKING_STRATEGY,
    *,
    semantic_chunk_max_chars: int = DEFAULT_SEMANTIC_CHUNK_MAX_CHARS,
    semantic_use_llamaindex: bool = DEFAULT_SEMANTIC_USE_LLAMAINDEX,
    pdf_paths: list[str] | None = None,
    include_structured_sources: bool = True,
    graph_ingest_enabled: bool = DEFAULT_GRAPH_INGEST_ENABLED,
    relation_min_confidence: float = DEFAULT_RELATION_MIN_CONFIDENCE,
    entity_min_confidence: float = DEFAULT_ENTITY_MIN_CONFIDENCE,
    qdrant_upsert_batch_size: int = DEFAULT_QDRANT_UPSERT_BATCH_SIZE,
    qdrant_upsert_max_retries: int = DEFAULT_QDRANT_UPSERT_MAX_RETRIES,
    qdrant_upsert_retry_delay_seconds: float = DEFAULT_QDRANT_UPSERT_RETRY_DELAY_SECONDS,
    chunk_min_chars: int = DEFAULT_CHUNK_MIN_CHARS,
    chunk_min_words: int = DEFAULT_CHUNK_MIN_WORDS,
    list_chunk_min_words: int = DEFAULT_LIST_CHUNK_MIN_WORDS,
) -> int:
    """Ingest structured items and PDF chunks into Qdrant with stable IDs."""

    ensure_collection(vector_size())

    points: list[PointStruct] = []
    if include_structured_sources:
        items = load_medical_items(json_path, csv_path)
        for item in items:
            base_text = f"{item.title}\n{item.description}".strip()
            chunks = chunk_text(
                base_text,
                strategy=chunking_strategy,
                semantic_max_chars=semantic_chunk_max_chars,
                semantic_use_llamaindex=semantic_use_llamaindex,
            )
            if not chunks:
                chunks = [base_text]

            filtered_chunks = [
                chunk
                for chunk in chunks
                if _passes_chunk_quality(
                    chunk,
                    is_list=False,
                    min_chars=chunk_min_chars,
                    min_words=chunk_min_words,
                    list_min_words=list_chunk_min_words,
                )
            ]
            if not filtered_chunks:
                continue

            vectors = embed_texts(filtered_chunks)
            for chunk_index, (chunk, vector) in enumerate(
                zip(filtered_chunks, vectors, strict=False),
                start=1,
            ):
                points.append(
                    _build_structured_point(
                        item=item,
                        chunk=chunk,
                        vector=vector,
                        chunk_index=chunk_index,
                        chunking_strategy=chunking_strategy,
                        semantic_chunk_max_chars=semantic_chunk_max_chars,
                        semantic_use_llamaindex=semantic_use_llamaindex,
                    )
                )

    disease_terms = load_disease_terms(json_path)
    graph_chunks: list[Any] = []
    for pdf_path in pdf_paths or []:
        pdf_chunks = load_pdf_chunks(
            pdf_path,
            chunking_strategy=chunking_strategy,
            semantic_chunk_max_chars=semantic_chunk_max_chars,
            semantic_use_llamaindex=semantic_use_llamaindex,
        )
        if not pdf_chunks:
            continue
        filtered_pdf_chunks = [
            chunk
            for chunk in pdf_chunks
            if _passes_chunk_quality(
                chunk.text,
                is_list=chunk.is_list,
                min_chars=chunk_min_chars,
                min_words=chunk_min_words,
                list_min_words=list_chunk_min_words,
            )
        ]
        if not filtered_pdf_chunks:
            continue
        graph_chunks.extend(filtered_pdf_chunks)

        vectors = embed_texts([chunk.text for chunk in filtered_pdf_chunks])
        for pdf_chunk, vector in zip(filtered_pdf_chunks, vectors, strict=False):
            entities = extract_entities_from_chunk(
                pdf_chunk,
                disease_terms=disease_terms,
                min_confidence=entity_min_confidence,
            )
            points.append(
                _build_pdf_point(
                    pdf_chunk=pdf_chunk,
                    vector=vector,
                    entities=entities,
                    chunking_strategy=chunking_strategy,
                    semantic_chunk_max_chars=semantic_chunk_max_chars,
                    semantic_use_llamaindex=semantic_use_llamaindex,
                )
            )

    if graph_ingest_enabled and graph_chunks:
        ingest_pdf_chunks_to_graph_safe(
            graph_chunks,
            disease_terms=disease_terms,
            min_entity_confidence=entity_min_confidence,
            min_relation_confidence=relation_min_confidence,
        )

    _upsert_points_with_retry(
        points,
        batch_size=qdrant_upsert_batch_size,
        max_retries=qdrant_upsert_max_retries,
        retry_delay_seconds=qdrant_upsert_retry_delay_seconds,
    )
    return len(points)
