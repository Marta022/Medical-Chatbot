from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from config import prompts
from config.settings import (
    AppSettings,
    ensure_startup_valid,
    load_settings,
    validate_startup,
)


class TestConfigAndPrompts(unittest.TestCase):
    def setUp(self) -> None:
        self._old_env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._old_env)

    def test_load_settings_reads_defaults(self) -> None:
        os.environ.pop("DEFAULT_TOP_K", None)
        settings = load_settings()
        self.assertGreater(settings.default_top_k, 0)
        self.assertTrue(settings.dataset_json_path.endswith("disease_database.json"))
        self.assertTrue(settings.dataset_csv_path.endswith("dataset_sheet1.csv"))
        self.assertEqual(settings.chunking_strategy, "section")
        self.assertGreater(settings.semantic_chunk_max_chars, 0)
        self.assertGreater(settings.retrieval_rerank_top_k, 0)
        self.assertGreaterEqual(settings.entity_min_confidence, 0)

    def test_prompt_helpers_return_expected_content(self) -> None:
        self.assertTrue(prompts.get_base_system_prompt())
        block = prompts.build_context_block(["line1", "line2"])
        self.assertIn("line1", block)
        self.assertIn("line2", block)

    def test_validate_startup_reports_missing_prompt_file(self) -> None:
        settings = AppSettings(llm_txt_path="does-not-exist.txt")
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("Prompt file not found" in item for item in errors))

    def test_validate_startup_reports_missing_openai_key_for_chat(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        settings = AppSettings()
        errors = validate_startup(command="chat", settings=settings)
        self.assertTrue(any("OPENAI_API_KEY is required" in item for item in errors))

    def test_validate_startup_rejects_invalid_chunking_strategy(self) -> None:
        settings = AppSettings(chunking_strategy="invalid")
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("CHUNKING_STRATEGY must be one of" in item for item in errors))

    def test_validate_startup_rejects_invalid_entity_min_confidence(self) -> None:
        settings = AppSettings(entity_min_confidence=1.2)
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("ENTITY_MIN_CONFIDENCE must be between 0 and 1" in item for item in errors))

    def test_validate_startup_rejects_invalid_graph_backend(self) -> None:
        settings = AppSettings(graph_backend="invalid")
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("GRAPH_BACKEND must be one of" in item for item in errors))

    def test_validate_startup_requires_kuzu_db_path(self) -> None:
        settings = AppSettings(kuzu_db_path="")
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("KUZU_DB_PATH is required." in item for item in errors))

    def test_validate_startup_rejects_invalid_relation_min_confidence(self) -> None:
        settings = AppSettings(relation_min_confidence=1.5)
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("RELATION_MIN_CONFIDENCE must be between 0 and 1" in item for item in errors))

    def test_validate_startup_rejects_invalid_retrieval_mode(self) -> None:
        settings = AppSettings(retrieval_mode="invalid")
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("RETRIEVAL_MODE must be one of" in item for item in errors))

    def test_validate_startup_rejects_invalid_graph_retrieval_top_k(self) -> None:
        settings = AppSettings(graph_retrieval_top_k=0)
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("GRAPH_RETRIEVAL_TOP_K must be greater than 0." in item for item in errors))

    def test_validate_startup_rejects_invalid_graph_traversal_depth(self) -> None:
        settings = AppSettings(graph_traversal_depth=0)
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("GRAPH_TRAVERSAL_DEPTH must be greater than 0." in item for item in errors))

    def test_validate_startup_rejects_invalid_hybrid_weights(self) -> None:
        settings = AppSettings(hybrid_graph_weight=-0.1)
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("HYBRID_GRAPH_WEIGHT must be >= 0." in item for item in errors))

    def test_validate_startup_rejects_invalid_chunk_quality_thresholds(self) -> None:
        settings = AppSettings(chunk_min_chars=0, chunk_min_words=0, list_chunk_min_words=0)
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("CHUNK_MIN_CHARS must be greater than 0." in item for item in errors))
        self.assertTrue(any("CHUNK_MIN_WORDS must be greater than 0." in item for item in errors))
        self.assertTrue(any("LIST_CHUNK_MIN_WORDS must be greater than 0." in item for item in errors))

    def test_validate_startup_rejects_invalid_rerank_top_k(self) -> None:
        settings = AppSettings(retrieval_rerank_top_k=0)
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("RETRIEVAL_RERANK_TOP_K must be greater than 0." in item for item in errors))

    def test_validate_startup_rejects_invalid_keyword_fallback_settings(self) -> None:
        settings = AppSettings(keyword_fallback_min_score=-0.1, keyword_fallback_candidate_limit=0)
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("KEYWORD_FALLBACK_MIN_SCORE must be >= 0." in item for item in errors))
        self.assertTrue(any("KEYWORD_FALLBACK_CANDIDATE_LIMIT must be greater than 0." in item for item in errors))

    def test_validate_startup_requires_gitnexus_url_when_enabled(self) -> None:
        settings = AppSettings(gitnexus_enabled=True, gitnexus_base_url="")
        errors = validate_startup(command="eval", settings=settings)
        self.assertTrue(any("GITNEXUS_BASE_URL is required" in item for item in errors))

    def test_validate_startup_rejects_fallback_embeddings_for_chat_by_default(self) -> None:
        os.environ.pop("OPENAI_API_KEY", None)
        settings = AppSettings()
        with patch("config.settings._using_fallback_embeddings", return_value=True):
            errors = validate_startup(command="chat", settings=settings)
        self.assertTrue(any("deterministic fallback mode" in item for item in errors))

    def test_validate_startup_allows_fallback_embeddings_when_enabled(self) -> None:
        settings = AppSettings(allow_fallback_embeddings=True)
        with patch("config.settings._using_fallback_embeddings", return_value=True):
            errors = validate_startup(command="ingest", settings=settings)
        self.assertFalse(any("deterministic fallback mode" in item for item in errors))

    def test_validate_startup_requires_llamaindex_for_semantic_chunking_when_strict(self) -> None:
        settings = AppSettings(
            chunking_strategy="semantic",
            semantic_use_llamaindex=True,
            allow_semantic_chunk_fallback=False,
            allow_fallback_embeddings=True,
        )
        with patch("config.settings._llamaindex_semantic_available", return_value=False):
            errors = validate_startup(command="ingest", settings=settings)
        self.assertTrue(any("Semantic chunking requires llama-index-core" in item for item in errors))

    def test_validate_startup_rejects_semantic_mode_without_llamaindex_toggle(self) -> None:
        settings = AppSettings(
            chunking_strategy="semantic",
            semantic_use_llamaindex=False,
            allow_fallback_embeddings=True,
        )
        errors = validate_startup(command="ingest", settings=settings)
        self.assertTrue(any("Semantic chunking is strict" in item for item in errors))

    def test_validate_startup_still_requires_llamaindex_even_with_fallback_toggle(self) -> None:
        settings = AppSettings(
            chunking_strategy="semantic",
            semantic_use_llamaindex=True,
            allow_semantic_chunk_fallback=True,
            allow_fallback_embeddings=True,
        )
        with patch("config.settings._llamaindex_semantic_available", return_value=False):
            errors = validate_startup(command="ingest", settings=settings)
        self.assertTrue(any("Semantic chunking requires llama-index-core" in item for item in errors))

    def test_ensure_startup_valid_passes_for_eval_with_temp_prompt(self) -> None:
        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            suffix=".txt",
            encoding="utf-8",
        ) as handle:
            handle.write("system prompt")
            temp_prompt = handle.name

        try:
            settings = AppSettings(
                llm_txt_path=temp_prompt,
                dataset_json_path="data/dataset/disease_database.json",
                dataset_csv_path="data/dataset/dataset_sheet1.csv",
            )
            ensure_startup_valid(command="eval", settings=settings)
        finally:
            Path(temp_prompt).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
