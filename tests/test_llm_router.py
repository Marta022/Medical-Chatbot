from __future__ import annotations

import unittest
from unittest.mock import patch

from agent.reasoning import llm_router
from config.settings import SETTINGS
from models import LLMRequest


class TestLLMRouter(unittest.TestCase):
    def test_llm_ask_request_uses_openai(self) -> None:
        request = LLMRequest(
            system_prompt="sys",
            user_message="hello",
            context_block="",
            provider="openai",
        )
        with patch("agent.reasoning.llm_router.openai_call", return_value="ok") as mocked:
            response = llm_router.llm_ask_request(request)
        mocked.assert_called_once()
        self.assertEqual(response.content, "ok")
        self.assertEqual(response.provider, "openai")
        self.assertEqual(response.model, SETTINGS.openai_model)

    def test_llm_ask_request_uses_ollama(self) -> None:
        request = LLMRequest(
            system_prompt="sys",
            user_message="hello",
            context_block="",
            provider="ollama",
        )
        with patch("agent.reasoning.llm_router.ollama_call", return_value="ok") as mocked:
            response = llm_router.llm_ask_request(request)
        mocked.assert_called_once()
        self.assertEqual(response.content, "ok")
        self.assertEqual(response.provider, "ollama")
        self.assertEqual(response.model, SETTINGS.ollama_model)

    def test_llm_classify_uses_provider(self) -> None:
        with patch("agent.reasoning.llm_router.ollama_call", return_value="SAFE") as mocked:
            response = llm_router.llm_classify(
                messages=[{"role": "user", "content": "test"}],
                provider="ollama",
            )
        mocked.assert_called_once()
        self.assertEqual(response, "SAFE")

    def test_select_provider_rejects_unknown(self) -> None:
        with self.assertRaises(ValueError):
            llm_router._select_provider("invalid")


if __name__ == "__main__":
    unittest.main()
