from __future__ import annotations

import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from agent.reasoning.providers import (
    anthropic_client,
    local_gemma_client,
    local_qwen_client,
    openai_client,
)


class TestProviderClients(unittest.TestCase):
    def setUp(self) -> None:
        openai_client._client = None
        anthropic_client._client = None

    def test_anthropic_call_uses_client(self) -> None:
        fake_block = SimpleNamespace(text="ok")
        fake_response = SimpleNamespace(content=[fake_block])
        fake_client = MagicMock()
        fake_client.messages.create.return_value = fake_response

        with patch("agent.reasoning.providers.anthropic_client.Anthropic", return_value=fake_client):
            os.environ["ANTHROPIC_API_KEY"] = "test"
            result = anthropic_client.anthropic_call(
                messages=[{"role": "user", "content": "hi"}],
                model="claude-test",
            )

        self.assertEqual(result, "ok")
        fake_client.messages.create.assert_called_once()

    def test_openai_call_uses_client(self) -> None:
        fake_message = SimpleNamespace(content="ok")
        fake_choice = SimpleNamespace(message=fake_message)
        fake_response = SimpleNamespace(choices=[fake_choice])
        fake_client = MagicMock()
        fake_client.chat.completions.create.return_value = fake_response

        with patch("agent.reasoning.providers.openai_client.OpenAI", return_value=fake_client):
            os.environ["OPENAI_API_KEY"] = "test"
            result = openai_client.openai_call(
                messages=[{"role": "user", "content": "hi"}],
                model="unit",
            )

        self.assertEqual(result, "ok")
        fake_client.chat.completions.create.assert_called_once()

    def test_ollama_call_uses_module(self) -> None:
        fake_module = MagicMock()
        fake_module.chat.return_value = {"message": {"content": "ok"}}
        with patch.object(local_gemma_client, "ollama", fake_module):
            result = local_gemma_client.ollama_call(
                messages=[{"role": "user", "content": "hi"}],
                model="unit",
                temperature=0.1,
            )
        self.assertEqual(result, "ok")

    def test_qwen_call_uses_ollama_transport(self) -> None:
        with patch(
            "agent.reasoning.providers.local_qwen_client.ollama_call", return_value="ok"
        ) as mocked:
            result = local_qwen_client.qwen_call(
                messages=[{"role": "user", "content": "hi"}],
                model="qwen3.5",
                temperature=0.1,
            )

        self.assertEqual(result, "ok")
        mocked.assert_called_once()


if __name__ == "__main__":
    unittest.main()
