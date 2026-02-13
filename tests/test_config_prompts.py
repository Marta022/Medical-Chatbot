from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from config import prompts
from config.settings import AppSettings, ensure_startup_valid, load_settings, validate_startup


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

    def test_ensure_startup_valid_passes_for_eval_with_temp_prompt(self) -> None:
        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as handle:
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

