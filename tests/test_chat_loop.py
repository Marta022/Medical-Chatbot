from __future__ import annotations

import unittest
from unittest.mock import patch

from agent.orchestrator import chat_loop
from models import GuardrailResult, OrchestratorResponse, RetrievalResult


class _RecordingStore:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def save_interaction(self, **kwargs: object) -> str:
        self.calls.append(kwargs)
        return "interaction-cli"


class _RaisingStore:
    def save_interaction(self, **_kwargs: object) -> str:
        raise OSError("database unavailable")


class TestChatLoop(unittest.TestCase):
    def test_chat_loop_handles_guardrail_block(self) -> None:
        store = _RecordingStore()
        responses = [
            OrchestratorResponse(
                response="blocked",
                provider=None,
                model=None,
                retries=0,
                guardrail=GuardrailResult(is_valid=False, message="blocked", reason_code="BLOCKED"),
                evaluator=None,
                retrieval=None,
                context_lines=[],
            )
        ]

        class FakeOrchestrator:
            def run(self, _request):
                return responses[0]

        with patch("agent.orchestrator.chat_loop.Orchestrator", return_value=FakeOrchestrator()):
            with patch("agent.orchestrator.chat_loop._build_interaction_store", return_value=store):
                with patch("builtins.input", side_effect=["question", "exit"]):
                    chat_loop.run_chat_loop(top_k=1)

        self.assertEqual(len(store.calls), 1)
        self.assertEqual(store.calls[0]["endpoint"], "cli")
        self.assertEqual(store.calls[0]["request"].query, "question")
        self.assertEqual(store.calls[0]["response"].response, "blocked")

    def test_chat_loop_logs_context_when_valid(self) -> None:
        response = OrchestratorResponse(
            response="ok",
            provider="openai",
            model="unit",
            retries=0,
            guardrail=GuardrailResult(is_valid=True, reason_code="SAFE"),
            evaluator=None,
            retrieval=RetrievalResult(),
            context_lines=["ctx1", "ctx2"],
        )

        class FakeOrchestrator:
            def run(self, _request):
                return response

        with patch("agent.orchestrator.chat_loop.Orchestrator", return_value=FakeOrchestrator()):
            with patch("agent.orchestrator.chat_loop._build_interaction_store", return_value=None):
                with patch("builtins.input", side_effect=["question", "exit"]):
                    chat_loop.run_chat_loop(top_k=1)

    def test_chat_loop_does_not_persist_exit_command(self) -> None:
        store = _RecordingStore()

        with patch("agent.orchestrator.chat_loop.Orchestrator"):
            with patch("agent.orchestrator.chat_loop._build_interaction_store", return_value=store):
                with patch("builtins.input", return_value="exit"):
                    chat_loop.run_chat_loop(top_k=1)

        self.assertEqual(store.calls, [])

    def test_chat_loop_continues_when_persistence_fails(self) -> None:
        response = OrchestratorResponse(
            response="ok",
            provider="openai",
            model="unit",
            retries=0,
            guardrail=GuardrailResult(is_valid=True, reason_code="SAFE"),
            evaluator=None,
            retrieval=RetrievalResult(),
            context_lines=[],
        )

        class FakeOrchestrator:
            def run(self, _request):
                return response

        with patch("agent.orchestrator.chat_loop.Orchestrator", return_value=FakeOrchestrator()):
            with patch(
                "agent.orchestrator.chat_loop._build_interaction_store",
                return_value=_RaisingStore(),
            ):
                with patch("builtins.input", side_effect=["question", "exit"]):
                    chat_loop.run_chat_loop(top_k=1)


if __name__ == "__main__":
    unittest.main()
