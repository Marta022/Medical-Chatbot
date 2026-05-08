from __future__ import annotations

import uuid


def build_entity_id(entity_type: str, canonical_form: str) -> str:
    payload = f"{entity_type.strip().lower()}|{canonical_form.strip().lower()}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, payload))


def build_source_chunk_id(source_file: str, page: int, chunk_id: str) -> str:
    payload = f"{source_file.strip().lower()}|{page}|{chunk_id.strip().lower()}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, payload))
