from __future__ import annotations

import unittest
from unittest.mock import patch

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
            hits=[RetrievalHit(title="Grip", text="Febra si tuse", score=0.91, source="dataset")]
        )
        evaluator = EvaluatorResult(passed=True, score=1.0, reasons=[], retry_recommended=False)
        return OrchestratorResponse(
            response=f"answer:{request.query}",
            provider="stub-provider",
            model="stub-model",
            retries=0,
            guardrail=GuardrailResult(is_valid=True),
            evaluator=evaluator,
            retrieval=retrieval,
            context_lines=["Febra si tuse (0.9100)"],
        )


class _RaisingOrchestrator:
    def run(self, _request: QueryRequest) -> OrchestratorResponse:
        raise RuntimeError("upstream_down")


class _CaptureOrchestrator:
    last_request: QueryRequest | None = None

    def run(self, request: QueryRequest) -> OrchestratorResponse:
        _CaptureOrchestrator.last_request = request
        retrieval = RetrievalResult(
            hits=[RetrievalHit(title="x", text="y", score=0.8, source="unit")]
        )
        evaluator = EvaluatorResult(passed=True, score=1.0, reasons=[], retry_recommended=False)
        return OrchestratorResponse(
            response="ok",
            provider="stub-provider",
            model="stub-model",
            retries=0,
            guardrail=GuardrailResult(is_valid=True),
            evaluator=evaluator,
            retrieval=retrieval,
            context_lines=[],
        )


class _RecordingStore:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def save_interaction(self, **kwargs: object) -> str:
        self.calls.append(kwargs)
        return "interaction-api"


class _RaisingStore:
    def save_interaction(self, **_kwargs: object) -> str:
        raise OSError("database unavailable")


def _stub_ingest(_json_path: str, _csv_path: str, _chunking_strategy: str = "section") -> int:
    return 7


def _stub_eval() -> dict[str, object]:
    return {"passed": True, "score": 1.0, "reasons": []}


def _stub_to_json(value: object) -> object:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    return value


class TestApiEngineEndpoints(unittest.TestCase):
    def test_chat_endpoint_returns_orchestrator_payload(self) -> None:
        deps = ApiDependencies(
            orchestrator_factory=_StubOrchestrator,
            ingest=_stub_ingest,
            run_eval=_stub_eval,
            to_json_compatible=_stub_to_json,
        )
        client = create_app(dependencies=deps).test_client()

        response = client.post("/chat", json={"query": "Ce este gripa?", "top_k": 2})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["provider"], "stub-provider")
        self.assertIn("answer:", payload["response"])

    def test_chat_endpoint_persists_final_result_and_session_id(self) -> None:
        store = _RecordingStore()
        deps = ApiDependencies(
            orchestrator_factory=_StubOrchestrator,
            ingest=_stub_ingest,
            run_eval=_stub_eval,
            to_json_compatible=_stub_to_json,
            interaction_store=store,
        )
        client = create_app(dependencies=deps).test_client()

        response = client.post(
            "/chat",
            json={"query": "Ce este gripa?", "session_id": " session-7 "},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(store.calls), 1)
        call = store.calls[0]
        self.assertEqual(call["endpoint"], "/chat")
        self.assertEqual(call["session_id"], "session-7")
        self.assertEqual(call["request"].query, "Ce este gripa?")
        self.assertEqual(call["response"].response, "answer:Ce este gripa?")

    def test_chat_endpoint_returns_result_when_persistence_fails(self) -> None:
        deps = ApiDependencies(
            orchestrator_factory=_StubOrchestrator,
            ingest=_stub_ingest,
            run_eval=_stub_eval,
            to_json_compatible=_stub_to_json,
            interaction_store=_RaisingStore(),
        )
        client = create_app(dependencies=deps).test_client()

        response = client.post("/chat", json={"query": "Ce este gripa?"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("answer:", response.get_json()["response"])

    def test_chat_endpoint_rejects_invalid_query(self) -> None:
        deps = ApiDependencies(
            orchestrator_factory=_StubOrchestrator,
            ingest=_stub_ingest,
            run_eval=_stub_eval,
            to_json_compatible=_stub_to_json,
        )
        client = create_app(dependencies=deps).test_client()

        response = client.post("/chat", json={"query": ""})
        self.assertEqual(response.status_code, 400)
        payload = response.get_json()
        self.assertEqual(payload["error"]["message"], "query must be a non-empty string")

    def test_ingest_endpoint_returns_insert_count(self) -> None:
        deps = ApiDependencies(
            orchestrator_factory=_StubOrchestrator,
            ingest=_stub_ingest,
            run_eval=_stub_eval,
            to_json_compatible=_stub_to_json,
        )
        client = create_app(dependencies=deps).test_client()

        response = client.post("/ingest", json={"chunking_strategy": "section"})
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["inserted"], 7)

    def test_eval_endpoint_returns_eval_payload(self) -> None:
        deps = ApiDependencies(
            orchestrator_factory=_StubOrchestrator,
            ingest=_stub_ingest,
            run_eval=_stub_eval,
            to_json_compatible=_stub_to_json,
        )
        client = create_app(dependencies=deps).test_client()

        response = client.post("/eval")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertTrue(payload["passed"])

    def test_runtime_errors_use_json_error_schema(self) -> None:
        deps = ApiDependencies(
            orchestrator_factory=_RaisingOrchestrator,
            ingest=_stub_ingest,
            run_eval=_stub_eval,
            to_json_compatible=_stub_to_json,
        )
        client = create_app(dependencies=deps).test_client()

        response = client.post("/chat", json={"query": "test"})
        self.assertEqual(response.status_code, 503)
        payload = response.get_json()
        self.assertEqual(payload["error"]["message"], "upstream_down")

    def test_graph_nexus_endpoint_returns_payload(self) -> None:
        deps = ApiDependencies(
            orchestrator_factory=_StubOrchestrator,
            ingest=_stub_ingest,
            run_eval=_stub_eval,
            to_json_compatible=_stub_to_json,
        )
        client = create_app(dependencies=deps).test_client()

        with patch(
            "api.app.build_gitnexus_payload_safe",
            return_value={"status": "ok", "nodes": [], "edges": []},
        ):
            response = client.get("/graph/nexus?query=mi&limit=5")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("nodes", payload)
        self.assertIn("edges", payload)

    def test_chat_endpoint_accepts_graph_policy_controls(self) -> None:
        deps = ApiDependencies(
            orchestrator_factory=_CaptureOrchestrator,
            ingest=_stub_ingest,
            run_eval=_stub_eval,
            to_json_compatible=_stub_to_json,
        )
        client = create_app(dependencies=deps).test_client()

        response = client.post(
            "/chat",
            json={
                "query": "test",
                "retrieval_mode": "hybrid",
                "graph_depth": 2,
                "vector_weight": 1.0,
                "graph_weight": 0.7,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(_CaptureOrchestrator.last_request)
        filters = _CaptureOrchestrator.last_request.filters or {}
        self.assertEqual(filters["__retrieval_mode"], "hybrid")
        self.assertEqual(filters["__graph_depth"], "2")


if __name__ == "__main__":
    unittest.main()
