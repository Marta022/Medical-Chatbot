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

    def test_llm_ask_request_uses_qwen35(self) -> None:
        request = LLMRequest(
            system_prompt="sys",
            user_message="hello",
            context_block="",
            provider="qwen3.5",
        )
        with patch("agent.reasoning.llm_router.qwen_call", return_value="ok") as mocked:
            response = llm_router.llm_ask_request(request)
        mocked.assert_called_once()
        self.assertEqual(response.content, "ok")
        self.assertEqual(response.provider, "qwen3.5")
        self.assertEqual(response.model, SETTINGS.qwen_model)

    def test_llm_classify_uses_provider(self) -> None:
        with patch("agent.reasoning.llm_router.ollama_call", return_value="SAFE") as mocked:
            response = llm_router.llm_classify(
                messages=[{"role": "user", "content": "test"}],
                provider="ollama",
            )
        mocked.assert_called_once()
        self.assertEqual(response, "SAFE")

    def test_llm_classify_uses_qwen35_provider(self) -> None:
        with patch("agent.reasoning.llm_router.qwen_call", return_value="SAFE") as mocked:
            response = llm_router.llm_classify(
                messages=[{"role": "user", "content": "test"}],
                provider="qwen3.5",
            )
        mocked.assert_called_once()
        self.assertEqual(response, "SAFE")

    def test_select_provider_rejects_unknown(self) -> None:
        with self.assertRaises(ValueError):
            llm_router._select_provider("invalid")

    def test_llm_cleanup_pdf_page_uses_openai_request_flow(self) -> None:
        with patch("agent.reasoning.llm_router.openai_call", return_value="# Page") as mocked:
            response = llm_router.llm_cleanup_pdf_page(
                source_file="demo.pdf",
                page_number=6,
                page_text="CAPITOLUL 1\nText extras",
                provider="openai",
            )

        mocked.assert_called_once()
        sent_messages = mocked.call_args.kwargs["messages"]
        self.assertEqual(sent_messages[0]["role"], "system")
        self.assertIn("Markdown", sent_messages[0]["content"])
        self.assertIn("Source file: demo.pdf", sent_messages[1]["content"])
        self.assertIn("Page: 6", sent_messages[1]["content"])
        self.assertEqual(response.content, "# Page")
        self.assertEqual(response.provider, "openai")

    def test_llm_cleanup_pdf_page_rejects_invalid_payload(self) -> None:
        with self.assertRaises(ValueError):
            llm_router.llm_cleanup_pdf_page(
                source_file="demo.pdf",
                page_number=0,
                page_text="text",
                provider="openai",
            )

        with self.assertRaises(ValueError):
            llm_router.llm_cleanup_pdf_page(
                source_file="demo.pdf",
                page_number=1,
                page_text="   ",
                provider="openai",
            )


if __name__ == "__main__":
    unittest.main()
