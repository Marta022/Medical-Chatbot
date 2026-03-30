from __future__ import annotations

"""Graph client abstractions and Kuzu backend implementation."""

import importlib
from pathlib import Path
from typing import Any, Protocol

from config.settings import SETTINGS, AppSettings

GRAPH_BACKEND_KUZU = "kuzu"
GRAPH_DATABASE_FILENAME = "graph.kuzu"
ERROR_EMPTY_DB_PATH = "db_path must be a non-empty string"
ERROR_UNSUPPORTED_BACKEND = "Unsupported graph backend: {backend}"


class GraphClient(Protocol):
    """Minimal graph client contract used by retrieval/visualization flows."""

    def execute(self, query: str, parameters: dict[str, Any] | None = None) -> Any:
        ...

    def close(self) -> None:
        ...


def _import_kuzu() -> Any:
    """Import kuzu lazily to keep optional dependency behavior explicit."""

    try:
        return importlib.import_module("kuzu")
    except ImportError as exc:
        raise RuntimeError(
            "Kuzu dependency is not installed. Install requirements before using graph features."
        ) from exc


class KuzuGraphClient:
    """Kuzu-backed graph client with tolerant execute signatures."""

    def __init__(self, db_path: str) -> None:
        if not db_path.strip():
            raise ValueError(ERROR_EMPTY_DB_PATH)
        storage_path = Path(db_path)
        storage_path.mkdir(parents=True, exist_ok=True)

        # Newer kuzu versions expect a database file path rather than a directory path.
        database_path = storage_path / GRAPH_DATABASE_FILENAME

        kuzu = _import_kuzu()
        database = kuzu.Database(str(database_path))
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
    """Build graph client from app settings."""

    if settings.graph_backend == GRAPH_BACKEND_KUZU:
        return KuzuGraphClient(settings.kuzu_db_path)
    raise ValueError(ERROR_UNSUPPORTED_BACKEND.format(backend=settings.graph_backend))
