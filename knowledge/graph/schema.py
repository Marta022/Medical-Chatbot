from __future__ import annotations

from knowledge.graph.client import GraphClient


def graph_schema_statements() -> list[str]:
    return [
        (
            "CREATE NODE TABLE IF NOT EXISTS Entity("
            "entity_id STRING, "
            "canonical_form STRING, "
            "entity_type STRING, "
            "PRIMARY KEY(entity_id)"
            ");"
        ),
        (
            "CREATE NODE TABLE IF NOT EXISTS SourceChunk("
            "source_chunk_id STRING, "
            "source_file STRING, "
            "page INT64, "
            "chunk_id STRING, "
            "chapter STRING, "
            "section STRING, "
            "PRIMARY KEY(source_chunk_id)"
            ");"
        ),
        (
            "CREATE REL TABLE IF NOT EXISTS MENTIONED_IN("
            "FROM Entity TO SourceChunk, "
            "mention_text STRING, "
            "confidence DOUBLE, "
            "source_file STRING, "
            "page INT64, "
            "chunk_id STRING"
            ");"
        ),
        (
            "CREATE REL TABLE IF NOT EXISTS DISEASE_HAS_SYMPTOM("
            "FROM Entity TO Entity, "
            "confidence DOUBLE, "
            "source_file STRING, "
            "page INT64, "
            "chunk_id STRING"
            ");"
        ),
        (
            "CREATE REL TABLE IF NOT EXISTS DRUG_TREATS_DISEASE("
            "FROM Entity TO Entity, "
            "confidence DOUBLE, "
            "source_file STRING, "
            "page INT64, "
            "chunk_id STRING"
            ");"
        ),
        (
            "CREATE REL TABLE IF NOT EXISTS CONDITION_CAUSES_SYMPTOM("
            "FROM Entity TO Entity, "
            "confidence DOUBLE, "
            "source_file STRING, "
            "page INT64, "
            "chunk_id STRING"
            ");"
        ),
        (
            "CREATE REL TABLE IF NOT EXISTS DISEASE_DIFFERS_FROM_DISEASE("
            "FROM Entity TO Entity, "
            "confidence DOUBLE, "
            "source_file STRING, "
            "page INT64, "
            "chunk_id STRING"
            ");"
        ),
    ]


def ensure_graph_schema(graph_client: GraphClient) -> None:
    for statement in graph_schema_statements():
        graph_client.execute(statement)
