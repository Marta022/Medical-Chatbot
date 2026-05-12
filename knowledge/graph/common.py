"""Shared helpers for graph result normalization."""

from __future__ import annotations

from typing import Any


def _records_from_frame(frame: Any) -> list[dict[str, Any]]:
    to_dict = getattr(frame, "to_dict", None)
    if not callable(to_dict):
        return []
    records = to_dict(orient="records")
    if isinstance(records, list):
        return [item for item in records if isinstance(item, dict)]
    return []


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

    rows_as_dict = getattr(result, "rows_as_dict", None)
    if callable(rows_as_dict):
        rows = rows_as_dict()
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]

    as_dict = getattr(result, "as_dict", None)
    if callable(as_dict):
        rows = as_dict()
        if isinstance(rows, list):
            return [item for item in rows if isinstance(item, dict)]

    to_df = getattr(result, "to_df", None)
    if callable(to_df):
        rows = _records_from_frame(to_df())
        if rows:
            return rows

    get_as_df = getattr(result, "get_as_df", None)
    if callable(get_as_df):
        rows = _records_from_frame(get_as_df())
        if rows:
            return rows

    get_column_names = getattr(result, "get_column_names", None)
    get_all = getattr(result, "get_all", None)
    if callable(get_column_names) and callable(get_all):
        columns = [str(column) for column in get_column_names()]
        rows: list[dict[str, Any]] = []
        for item in get_all():
            if isinstance(item, dict):
                rows.append(item)
            elif isinstance(item, (list, tuple)):
                rows.append(dict(zip(columns, item)))
            elif hasattr(item, "_asdict"):
                rows.append(dict(item._asdict()))
        return rows

    has_next = getattr(result, "has_next", None)
    get_next = getattr(result, "get_next", None)
    if callable(has_next) and callable(get_next):
        columns: list[str] = []
        get_column_names = getattr(result, "get_column_names", None)
        if callable(get_column_names):
            columns = [str(column) for column in get_column_names()]
        rows: list[dict[str, Any]] = []
        while result.has_next():
            item = result.get_next()
            if isinstance(item, dict):
                rows.append(item)
            elif isinstance(item, (list, tuple)) and columns:
                rows.append(dict(zip(columns, item)))
            elif hasattr(item, "_asdict"):
                rows.append(dict(item._asdict()))
        return rows
    return []
