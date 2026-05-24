from __future__ import annotations

import unittest

from api.app import create_app
from api.dependencies import ApiDependencies
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


class _RecordingStore:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def save_interaction(self, **kwargs: object) -> str:
        self.calls.append(kwargs)
        return "interaction-openai"


def _stub_ingest(_json_path: str, _csv_path: str, _chunking_strategy: str = "section") -> int:
    return 0


def _stub_eval() -> dict[str, object]:
    return {"passed": True, "score": 1.0}


def _stub_to_json(value: object) -> object:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


class TestApiOpenAIAdapter(unittest.TestCase):
    def _client(self, interaction_store: object | None = None):
        deps = ApiDependencies(
            orchestrator_factory=_StubOrchestrator,
            ingest=_stub_ingest,
            run_eval=_stub_eval,
            to_json_compatible=_stub_to_json,
            interaction_store=interaction_store,
        )
        return create_app(dependencies=deps).test_client()

    def test_v1_models_returns_openai_shape(self) -> None:
        response = self._client().get("/v1/models")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["object"], "list")
        self.assertTrue(len(payload["data"]) >= 1)
        self.assertEqual(payload["data"][0]["object"], "model")

    def test_v1_chat_completions_returns_openai_shape(self) -> None:
        response = self._client().post(
            "/v1/chat/completions",
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You are helpful."},
                    {"role": "user", "content": "Salut"},
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["object"], "chat.completion")
        self.assertEqual(payload["model"], "gpt-4o-mini")
        self.assertEqual(payload["choices"][0]["message"]["role"], "assistant")
        self.assertIn("assistant:", payload["choices"][0]["message"]["content"])

    def test_v1_chat_completions_validates_messages_type(self) -> None:
        response = self._client().post("/v1/chat/completions", json={"messages": "bad"})
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"]["message"], "messages must be a list")

    def test_v1_chat_completions_persists_once_with_session_id(self) -> None:
        store = _RecordingStore()
        response = self._client(store).post(
            "/v1/chat/completions",
            json={
                "session_id": "chat-session",
                "messages": [{"role": "user", "content": "Salut"}],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(store.calls), 1)
        self.assertEqual(store.calls[0]["endpoint"], "/v1/chat/completions")
        self.assertEqual(store.calls[0]["session_id"], "chat-session")
        self.assertEqual(store.calls[0]["request"].query, "Salut")

    def test_ollama_chat_delegation_persists_once_under_ollama_endpoint(self) -> None:
        store = _RecordingStore()
        response = self._client(store).post(
            "/v1/api/chat",
            json={"messages": [{"role": "user", "content": "Salut"}]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(store.calls), 1)
        self.assertEqual(store.calls[0]["endpoint"], "/v1/api/chat")


if __name__ == "__main__":
    unittest.main()
