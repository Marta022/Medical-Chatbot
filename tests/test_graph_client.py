from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from config.settings import AppSettings
from knowledge.graph.client import KuzuGraphClient, get_graph_client


class _FakeConnection:
    def __init__(self, database: object) -> None:
        self.database = database
        self.calls: list[tuple[str, dict[str, object] | None]] = []
        self.closed = False

    def execute(self, query: str, parameters: dict[str, object] | None = None) -> str:
        self.calls.append((query, parameters))
        return "ok"

    def close(self) -> None:
        self.closed = True


class TestGraphClient(unittest.TestCase):
    def test_kuzu_graph_client_requires_dependency(self) -> None:
        with patch("knowledge.graph.client.importlib.import_module", side_effect=ImportError):
            with self.assertRaises(RuntimeError):
                KuzuGraphClient("knowledge/graph/test-storage")

    def test_kuzu_graph_client_initializes_and_executes(self) -> None:
        state: dict[str, object] = {}

        def fake_database(path: str) -> str:
            state["db_path"] = path
            return "db"

        def fake_connection(database: object) -> _FakeConnection:
            conn = _FakeConnection(database)
            state["conn"] = conn
            return conn

        fake_kuzu = SimpleNamespace(Database=fake_database, Connection=fake_connection)
        with tempfile.TemporaryDirectory() as tmpdir:
            graph_path = Path(tmpdir) / "kuzu-data"
            with patch("knowledge.graph.client._import_kuzu", return_value=fake_kuzu):
                client = KuzuGraphClient(str(graph_path))
                result = client.execute("MATCH (n) RETURN n LIMIT 1")
                client.close()

        self.assertEqual(result, "ok")
        self.assertEqual(state["db_path"], str(graph_path))
        self.assertIsInstance(state["conn"], _FakeConnection)
        self.assertTrue(state["conn"].closed)

    def test_get_graph_client_rejects_unsupported_backend(self) -> None:
        settings = AppSettings(graph_backend="invalid")
        with self.assertRaises(ValueError):
            get_graph_client(settings)


if __name__ == "__main__":
    unittest.main()
