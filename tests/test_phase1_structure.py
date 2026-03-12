from __future__ import annotations

import importlib
import unittest
from pathlib import Path


class TestPhase1Structure(unittest.TestCase):
    def test_expected_packages_exist(self) -> None:
        required_paths = [
            Path("agent/orchestrator/chat_loop.py"),
            Path("agent/guardrail/rules_engine.py"),
            Path("agent/evaluation/evaluator.py"),
            Path("agent/reasoning/llm_router.py"),
            Path("knowledge/qdrant/client.py"),
            Path("rag/chunking/load_documents.py"),
            Path("rag/retrieval/retriever.py"),
            Path("models/contracts.py"),
        ]
        for path in required_paths:
            self.assertTrue(path.exists(), f"Missing expected path: {path}")

    def test_dataset_paths_moved_to_data_dataset(self) -> None:
        self.assertTrue(Path("data/dataset/disease_database.json").exists())
        self.assertTrue(Path("data/dataset/dataset_sheet1.csv").exists())
        self.assertFalse(Path("data/disease_database.json").exists())
        self.assertFalse(Path("data/dataset - Sheet1.csv").exists())

    def test_ingestion_uses_chunking_abstraction(self) -> None:
        source = Path("knowledge/qdrant/ingest.py").read_text(encoding="utf-8")
        self.assertIn("from rag.chunking.load_documents import load_medical_items", source)

    def test_import_smoke_migrated_modules(self) -> None:
        modules = [
            "run",
            "agent.orchestrator.chat_loop",
            "agent.guardrail.rules_engine",
            "knowledge.qdrant.client",
            "rag.retrieval.retriever",
            "models.contracts",
        ]
        for module in modules:
            imported = importlib.import_module(module)
            self.assertIsNotNone(imported)


if __name__ == "__main__":
    unittest.main()
