from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, Protocol

from config.settings import SETTINGS, AppSettings


class GraphClient(Protocol):
    def execute(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        ...

    def close(self) -> None:
        ...


def _import_kuzu() -> Any:
    try:
        return importlib.import_module("kuzu")
    except ImportError as exc:
        raise RuntimeError(
            "Kuzu dependency is not installed. Install requirements before using graph features."
        ) from exc


class KuzuGraphClient:
    def __init__(self, db_path: str) -> None:
        if not db_path.strip():
            raise ValueError("db_path must be a non-empty string")
        storage_path = Path(db_path)
        storage_path.mkdir(parents=True, exist_ok=True)

        kuzu = _import_kuzu()
        database = kuzu.Database(str(storage_path))
        self._connection = kuzu.Connection(database)

    def execute(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        if parameters is None:
            return self._connection.execute(query)
        try:
            return self._connection.execute(query, parameters)
        except TypeError:
            return self._connection.execute(query)

    def close(self) -> None:
        close_method = getattr(self._connection, "close", None)
        if callable(close_method):
            close_method()


def get_graph_client(settings: AppSettings = SETTINGS) -> GraphClient:
    if settings.graph_backend == "kuzu":
        return KuzuGraphClient(settings.kuzu_db_path)
    raise ValueError(f"Unsupported graph backend: {settings.graph_backend}")
