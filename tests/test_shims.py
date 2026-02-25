from __future__ import annotations

import unittest
from unittest.mock import patch

from guardrails import llm_guardrail
from ingestion import embed as ingest_embed
from ingestion import load_documents as ingest_load_documents
from llm_hub import anthropic_client, local_gemma_client, openai_client, router as llm_router_shim
from rag import retriever as retriever_shim
from translation import translator as translator_shim
from vector_db import qdrant_client as qdrant_shim


class TestShims(unittest.TestCase):
    def test_llm_guardrail_exports(self) -> None:
        self.assertTrue(callable(llm_guardrail.classify_guardrail_with_llm))
        self.assertTrue(llm_guardrail.GUARDRAIL_SYSTEM_PROMPT)

    def test_ingestion_shims(self) -> None:
        self.assertTrue(callable(ingest_embed.embed_texts))
        self.assertTrue(callable(ingest_load_documents.load_medical_items))

    def test_llm_hub_shims(self) -> None:
        self.assertTrue(callable(openai_client.openai_call))
        self.assertTrue(callable(anthropic_client.anthropic_call))
        self.assertTrue(callable(local_gemma_client.ollama_call))
        self.assertTrue(callable(llm_router_shim.llm_ask))
        self.assertTrue(callable(llm_router_shim.llm_ask_request))
        self.assertTrue(callable(llm_router_shim.llm_classify))

    def test_translation_shim_exports(self) -> None:
        self.assertTrue(callable(translator_shim.translate_to_english))
        self.assertTrue(callable(translator_shim.translate_to_romanian))

    def test_qdrant_shim_exports(self) -> None:
        self.assertTrue(qdrant_shim.COLLECTION)
        self.assertIsNotNone(qdrant_shim.client)
        self.assertTrue(callable(qdrant_shim.ensure_collection))

    def test_retriever_shim_delegates(self) -> None:
        with patch(
            "rag.retriever.retrieve_top_similar",
            return_value=type(
                "Result",
                (),
                {
                    "context_lines": lambda self, with_score: ["line1"],
                    "titles": lambda self: ["t1"],
                },
            )(),
        ):
            lines, titles = retriever_shim.retrieve_top_similar_descriptions("q", top_k=1)
        self.assertEqual(lines, ["line1"])
        self.assertEqual(titles, ["t1"])


if __name__ == "__main__":
    unittest.main()
