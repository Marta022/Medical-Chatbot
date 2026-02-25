from __future__ import annotations

import unittest
from dataclasses import dataclass

from api.app import create_app
from api.dependencies import ApiDependencies


@dataclass(frozen=True)
class _StubOrchestrator:
    pass


def _stub_ingest(_json_path: str, _csv_path: str, _chunking_strategy: str = "section") -> int:
    return 0


def _stub_eval() -> dict[str, object]:
    return {"passed": True, "score": 1.0}


def _stub_to_json(value: object) -> object:
    return value


class TestApiScaffold(unittest.TestCase):
    def test_create_app_registers_dependencies(self) -> None:
        deps = ApiDependencies(
            orchestrator_factory=_StubOrchestrator,
            ingest=_stub_ingest,
            run_eval=_stub_eval,
            to_json_compatible=_stub_to_json,
        )
        app = create_app(dependencies=deps)
        self.assertIs(app.config["API_DEPS"], deps)

    def test_health_endpoint_returns_ok_payload(self) -> None:
        app = create_app()
        client = app.test_client()

        response = client.get("/health")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "medical-chatbot-api")


if __name__ == "__main__":
    unittest.main()
