from __future__ import annotations

from typing import Any

from config.settings import SETTINGS
from knowledge.graph import get_graph_client


def _result_to_rows(result: Any) -> list[dict[str, Any]]:
    if result is None:
        return []
    if isinstance(result, list):
        return [item for item in result if isinstance(item, dict)]

    to_df = getattr(result, "to_df", None)
    if callable(to_df):
        frame = to_df()
        to_dict = getattr(frame, "to_dict", None)
        if callable(to_dict):
            records = to_dict(orient="records")
            if isinstance(records, list):
                return [item for item in records if isinstance(item, dict)]
    return []


def _source_link(source_file: str, page: int, chunk_id: str) -> str:
    return f"source://{source_file}#page={page}&chunk={chunk_id}"


def build_gitnexus_payload(
    *,
    query: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    graph_client = get_graph_client()
    try:
        result = graph_client.execute(
            (
                "MATCH (a:Entity)-[r]->(b:Entity) "
                "RETURN a.entity_id AS source_id, "
                "a.canonical_form AS source_label, "
                "a.entity_type AS source_type, "
                "b.entity_id AS target_id, "
                "b.canonical_form AS target_label, "
                "b.entity_type AS target_type, "
                "label(r) AS relation_label, "
                "r.source_file AS source_file, "
                "r.page AS page, "
                "r.chunk_id AS chunk_id, "
                "r.confidence AS confidence "
                "LIMIT $limit;"
            ),
            {"limit": int(limit)},
        )
        rows = _result_to_rows(result)
    finally:
        graph_client.close()

    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []
    for row in rows:
        source_id = str(row.get("source_id", "")).strip()
        target_id = str(row.get("target_id", "")).strip()
        if not source_id or not target_id:
            continue
        source_label = str(row.get("source_label", source_id))
        target_label = str(row.get("target_label", target_id))
        nodes[source_id] = {
            "id": source_id,
            "label": source_label,
            "type": str(row.get("source_type", "entity")),
        }
        nodes[target_id] = {
            "id": target_id,
            "label": target_label,
            "type": str(row.get("target_type", "entity")),
        }

        source_file = str(row.get("source_file", "unknown"))
        page = int(row.get("page", -1) or -1)
        chunk_id = str(row.get("chunk_id", "unknown"))
        edges.append(
            {
                "source": source_id,
                "target": target_id,
                "relation": str(row.get("relation_label", "")).lower(),
                "confidence": float(row.get("confidence", 0.0) or 0.0),
                "source_file": source_file,
                "page": page,
                "chunk_id": chunk_id,
                "source_link": _source_link(source_file, page, chunk_id),
            }
        )

    base = SETTINGS.gitnexus_base_url.rstrip("/")
    viewer_url = f"{base}/graph?query={query}" if base else ""
    return {
        "query": query,
        "viewer_url": viewer_url,
        "nodes": list(nodes.values()),
        "edges": edges,
    }


def build_gitnexus_payload_safe(
    *,
    query: str = "",
    limit: int = 50,
) -> dict[str, Any]:
    if not SETTINGS.gitnexus_enabled:
        return {
            "query": query,
            "viewer_url": None,
            "nodes": [],
            "edges": [],
            "status": "disabled",
        }
    try:
        payload = build_gitnexus_payload(query=query, limit=limit)
    except Exception:
        return {
            "query": query,
            "viewer_url": None,
            "nodes": [],
            "edges": [],
            "status": "unavailable",
        }
    payload["status"] = "ok"
    return payload
