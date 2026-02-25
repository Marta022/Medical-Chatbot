from __future__ import annotations

import unittest
from unittest.mock import patch

from agent.orchestrator import chat_loop
from models import GuardrailResult, OrchestratorResponse, RetrievalResult


class TestChatLoop(unittest.TestCase):
    def test_chat_loop_handles_guardrail_block(self) -> None:
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
            with patch("builtins.input", side_effect=["question", "exit"]):
                chat_loop.run_chat_loop(top_k=1)

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
            with patch("builtins.input", side_effect=["question", "exit"]):
                chat_loop.run_chat_loop(top_k=1)


if __name__ == "__main__":
    unittest.main()
