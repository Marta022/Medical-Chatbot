from __future__ import annotations

import unittest

from api.app import create_app
from api.dependencies import ApiDependencies
from config.api_config import ApiSettings
from models import (
    EvaluatorResult,
    GuardrailResult,
    OrchestratorResponse,
    QueryRequest,
    RetrievalHit,
    RetrievalResult,
)


class _StubOrchestrator:
    def run(self, request: QueryRequest) -> OrchestratorResponse:
        retrieval = RetrievalResult(
            hits=[RetrievalHit(title="Info", text="Context", score=0.8, source="dataset")]
        )
        evaluator = EvaluatorResult(passed=True, score=1.0, reasons=[], retry_recommended=False)
        return OrchestratorResponse(
            response=f"assistant:{request.query}",
            provider="stub-provider",
            model="stub-model",
            retries=0,
            guardrail=GuardrailResult(is_valid=True),
            evaluator=evaluator,
            retrieval=retrieval,
            context_lines=["Context (0.8000)"],
        )


def _stub_ingest(_json_path: str, _csv_path: str, _chunking_strategy: str = "section") -> int:
    return 0


def _stub_eval() -> dict[str, object]:
    return {"passed": True, "score": 1.0}


def _stub_to_json(value: object) -> object:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


def _deps() -> ApiDependencies:
    return ApiDependencies(
        orchestrator_factory=_StubOrchestrator,
        ingest=_stub_ingest,
        run_eval=_stub_eval,
        to_json_compatible=_stub_to_json,
    )


class TestApiConfigControls(unittest.TestCase):
    def test_api_disabled_blocks_non_health_requests(self) -> None:
        app = create_app(
            dependencies=_deps(),
            api_settings=ApiSettings(api_enabled=False),
        )
        client = app.test_client()

        response = client.post("/chat", json={"query": "Salut"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["error"]["message"], "api_disabled")

    def test_api_key_required_blocks_missing_credentials(self) -> None:
        app = create_app(
            dependencies=_deps(),
            api_settings=ApiSettings(require_api_key=True, api_key="secret"),
        )
        client = app.test_client()

        response = client.post("/chat", json={"query": "Salut"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json()["error"]["message"], "unauthorized")

    def test_api_key_required_accepts_valid_bearer_token(self) -> None:
        app = create_app(
            dependencies=_deps(),
            api_settings=ApiSettings(require_api_key=True, api_key="secret"),
        )
        client = app.test_client()

        response = client.post(
            "/chat",
            json={"query": "Salut"},
            headers={"Authorization": "Bearer secret"},
        )
        self.assertEqual(response.status_code, 200)

    def test_chat_rejects_top_k_above_limit(self) -> None:
        app = create_app(
            dependencies=_deps(),
            api_settings=ApiSettings(max_top_k=2),
        )
        client = app.test_client()

        response = client.post("/chat", json={"query": "Salut", "top_k": 3})
        self.assertEqual(response.status_code, 400)
        self.assertIn("top_k must be <= 2", response.get_json()["error"]["message"])

    def test_openai_chat_rejects_messages_above_limit(self) -> None:
        app = create_app(
            dependencies=_deps(),
            api_settings=ApiSettings(max_messages=1),
        )
        client = app.test_client()

        response = client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "one"},
                    {"role": "user", "content": "two"},
                ]
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("too many messages", response.get_json()["error"]["message"])


if __name__ == "__main__":
    unittest.main()
