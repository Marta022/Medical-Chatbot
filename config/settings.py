from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SUPPORTED_LLM_PROVIDERS = {"openai", "ollama"}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


@dataclass(frozen=True)
class AppSettings:
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "medical_docs"
    guardrail_llm_enabled: bool = True
    llm_txt_path: str = "llm.txt"
    llm_provider: str = "openai"
    openai_model: str = "gpt-4.1-mini"
    ollama_model: str = "gemma2:2b"
    default_top_k: int = 3
    dataset_json_path: str = "data/dataset/disease_database.json"
    dataset_csv_path: str = "data/dataset/dataset_sheet1.csv"


def load_settings() -> AppSettings:
    return AppSettings(
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333").strip(),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        qdrant_collection=os.getenv("QDRANT_COLLECTION", "medical_docs").strip(),
        guardrail_llm_enabled=_env_bool("GUARDRAIL_LLM_ENABLED", True),
        llm_txt_path=os.getenv("LLM_TXT_PATH", "llm.txt").strip(),
        llm_provider=os.getenv("LLM_PROVIDER", "openai").strip().lower(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma2:2b").strip(),
        default_top_k=_env_int("DEFAULT_TOP_K", 3),
        dataset_json_path=os.getenv("DATASET_JSON_PATH", "data/dataset/disease_database.json").strip(),
        dataset_csv_path=os.getenv("DATASET_CSV_PATH", "data/dataset/dataset_sheet1.csv").strip(),
    )


def _read_system_prompt(path: str) -> str:
    prompt_path = Path(path)
    if not prompt_path.exists():
        return "You are an AI medical assistant. Use only provided context."
    return prompt_path.read_text(encoding="utf-8").strip()


def validate_startup(
    command: str | None = None,
    settings: AppSettings | None = None,
) -> list[str]:
    current = settings or load_settings()
    errors: list[str] = []

    if not current.qdrant_url:
        errors.append("QDRANT_URL is required.")
    if not current.qdrant_collection:
        errors.append("QDRANT_COLLECTION is required.")
    if current.default_top_k <= 0:
        errors.append("DEFAULT_TOP_K must be greater than 0.")
    if current.llm_provider not in SUPPORTED_LLM_PROVIDERS:
        errors.append(
            f"LLM_PROVIDER must be one of {sorted(SUPPORTED_LLM_PROVIDERS)}, got '{current.llm_provider}'."
        )

    prompt_path = Path(current.llm_txt_path)
    if not prompt_path.exists():
        errors.append(f"Prompt file not found at '{current.llm_txt_path}'.")

    if command in {"ingest"}:
        if not Path(current.dataset_json_path).exists():
            errors.append(f"Dataset JSON not found at '{current.dataset_json_path}'.")
        if not Path(current.dataset_csv_path).exists():
            errors.append(f"Dataset CSV not found at '{current.dataset_csv_path}'.")

    if command in {"chat"} and current.llm_provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            errors.append("OPENAI_API_KEY is required when LLM_PROVIDER=openai for chat.")

    return errors


def ensure_startup_valid(
    command: str | None = None,
    settings: AppSettings | None = None,
) -> None:
    errors = validate_startup(command=command, settings=settings)
    if not errors:
        return
    details = "\n".join(f"- {item}" for item in errors)
    raise RuntimeError(f"Startup validation failed:\n{details}")


SETTINGS = load_settings()
BASE_SYSTEM_PROMPT = _read_system_prompt(SETTINGS.llm_txt_path)

# Backward-compatible constants for modules pending migration.
QDRANT_URL = SETTINGS.qdrant_url
QDRANT_API_KEY = SETTINGS.qdrant_api_key
QDRANT_COLLECTION = SETTINGS.qdrant_collection
GUARDRAIL_LLM_ENABLED = SETTINGS.guardrail_llm_enabled

