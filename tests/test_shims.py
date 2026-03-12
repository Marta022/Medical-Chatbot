from __future__ import annotations

import unittest

from ingestion import load_documents as ingest_load_documents
from llm_hub import router as llm_router_shim
from vector_db import qdrant_client as qdrant_shim
from evaluation import benchmark as evaluation_benchmark_shim
from evaluation import evaluator as evaluation_evaluator_shim
from guardrails import rules as guardrails_rules_shim


class TestShims(unittest.TestCase):
    def test_evaluation_shims(self) -> None:
        self.assertTrue(callable(evaluation_benchmark_shim.run_evaluation_smoke))
        self.assertTrue(callable(evaluation_evaluator_shim.evaluate_response))

    def test_guardrail_shim_exports(self) -> None:
        self.assertTrue(callable(guardrails_rules_shim.apply_guardrails))

    def test_ingestion_shim_exports(self) -> None:
        self.assertTrue(callable(ingest_load_documents.load_medical_items))

    def test_llm_router_shim_exports(self) -> None:
        self.assertTrue(callable(llm_router_shim.llm_ask))
        self.assertTrue(callable(llm_router_shim.llm_ask_request))
        self.assertTrue(callable(llm_router_shim.llm_classify))

    def test_qdrant_shim_exports(self) -> None:
        self.assertTrue(qdrant_shim.COLLECTION)
        self.assertIsNotNone(qdrant_shim.client)
        self.assertTrue(callable(qdrant_shim.ensure_collection))


if __name__ == "__main__":
    unittest.main()
