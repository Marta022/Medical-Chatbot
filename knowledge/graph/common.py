from __future__ import annotations

"""Shared helpers for graph result normalization."""

from typing import Any


def result_to_rows(result: Any) -> list[dict[str, Any]]:
    """Normalize graph client results into a list of plain dictionaries."""

    if result is None:
        return []
    if isinstance(result, list):
        rows: list[dict[str, Any]] = []
        for item in result:
            if isinstance(item, dict):
                rows.append(item)
            elif hasattr(item, "_asdict"):
                rows.append(dict(item._asdict()))
        return rows

    to_df = getattr(result, "to_df", None)
    if callable(to_df):
        frame = to_df()
        to_dict = getattr(frame, "to_dict", None)
        if callable(to_dict):
            records = to_dict(orient="records")
            if isinstance(records, list):
                return [item for item in records if isinstance(item, dict)]

    has_next = getattr(result, "has_next", None)
    get_next = getattr(result, "get_next", None)
    if callable(has_next) and callable(get_next):
        rows: list[dict[str, Any]] = []
        while result.has_next():
            item = result.get_next()
            if isinstance(item, dict):
                rows.append(item)
            elif hasattr(item, "_asdict"):
                rows.append(dict(item._asdict()))
        return rows
    return []
