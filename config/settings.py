"""Application settings, prompt loading, and startup validation."""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path

from dotenv import load_dotenv

from config.common import env_bool, env_float, env_int

load_dotenv()

SUPPORTED_LLM_PROVIDERS = {"openai", "ollama", "qwen3.5"}
SUPPORTED_CHUNKING_STRATEGIES = {"section", "semantic"}
SUPPORTED_GRAPH_BACKENDS = {"kuzu"}
SUPPORTED_RETRIEVAL_MODES = {"vector", "hybrid"}
DEFAULT_QDRANT_URL = "http://localhost:6333"
DEFAULT_QDRANT_COLLECTION = "medical_docs"
DEFAULT_LLM_TXT_PATH = "llm.txt"
DEFAULT_LLM_PROVIDER = "openai"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OLLAMA_MODEL = "gemma2:2b"
DEFAULT_QWEN_MODEL = "qwen3.5"
DEFAULT_TOP_K = 3
DEFAULT_RETRIEVAL_MIN_SCORE = 0.2
DEFAULT_RETRIEVAL_RERANK_TOP_K = 12
DEFAULT_KEYWORD_FALLBACK_MIN_SCORE = 0.18
DEFAULT_KEYWORD_FALLBACK_CANDIDATE_LIMIT = 1500
DEFAULT_DATASET_JSON_PATH = "data/dataset/disease_database.json"
DEFAULT_DATASET_CSV_PATH = "data/dataset/dataset_sheet1.csv"
DEFAULT_DATASET_PRIMARY_PDF_PATH = "data/dataset/DORIN-CURS_SEM2_searchable.pdf"
DEFAULT_DATASET_VALIDATION_PDF_PATH = (
    "data/dataset/DORIN_GENERALA_CARDIOVASCULARA-RESPIRATORIE-DISESTIVA.CV01.pdf"
)
DEFAULT_CHUNKING_STRATEGY = "semantic"
DEFAULT_SEMANTIC_CHUNK_MAX_CHARS = 700
DEFAULT_ENTITY_MIN_CONFIDENCE = 0.65
DEFAULT_CHUNK_MIN_CHARS = 40
DEFAULT_CHUNK_MIN_WORDS = 8
DEFAULT_LIST_CHUNK_MIN_WORDS = 2
DEFAULT_GRAPH_BACKEND = "kuzu"
DEFAULT_KUZU_DB_PATH = "knowledge/graph/kuzu_storage"
DEFAULT_RELATION_MIN_CONFIDENCE = 0.7
DEFAULT_RETRIEVAL_MODE = "vector"
DEFAULT_GRAPH_RETRIEVAL_TOP_K = 3
DEFAULT_GRAPH_TRAVERSAL_DEPTH = 1
DEFAULT_HYBRID_VECTOR_WEIGHT = 1.0
DEFAULT_HYBRID_GRAPH_WEIGHT = 0.9
DEFAULT_GITNEXUS_BASE_URL = "http://localhost:8088"
DEFAULT_SYSTEM_PROMPT = "You are an AI medical assistant. Use only provided context."
INGEST_COMMAND = "ingest"
CHAT_COMMAND = "chat"
EXTRACT_MARKDOWN_COMMAND = "extract-markdown"
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"


@dataclass(frozen=True)
class AppSettings:
    """Runtime configuration loaded from environment variables."""

    qdrant_url: str = DEFAULT_QDRANT_URL
    qdrant_api_key: str | None = None
    qdrant_collection: str = DEFAULT_QDRANT_COLLECTION
    guardrail_llm_enabled: bool = True
    llm_txt_path: str = DEFAULT_LLM_TXT_PATH
    llm_provider: str = DEFAULT_LLM_PROVIDER
    openai_model: str = DEFAULT_OPENAI_MODEL
    ollama_model: str = DEFAULT_OLLAMA_MODEL
    qwen_model: str = DEFAULT_QWEN_MODEL
    default_top_k: int = DEFAULT_TOP_K
    retrieval_min_score: float = DEFAULT_RETRIEVAL_MIN_SCORE
    retrieval_rerank_enabled: bool = True
    retrieval_rerank_top_k: int = DEFAULT_RETRIEVAL_RERANK_TOP_K
    keyword_fallback_enabled: bool = True
    keyword_fallback_min_score: float = DEFAULT_KEYWORD_FALLBACK_MIN_SCORE
    keyword_fallback_candidate_limit: int = DEFAULT_KEYWORD_FALLBACK_CANDIDATE_LIMIT
    dataset_json_path: str = DEFAULT_DATASET_JSON_PATH
    dataset_csv_path: str = DEFAULT_DATASET_CSV_PATH
    dataset_primary_pdf_path: str = DEFAULT_DATASET_PRIMARY_PDF_PATH
    dataset_validation_pdf_path: str = DEFAULT_DATASET_VALIDATION_PDF_PATH
    chunking_strategy: str = DEFAULT_CHUNKING_STRATEGY
    semantic_chunk_max_chars: int = DEFAULT_SEMANTIC_CHUNK_MAX_CHARS
    semantic_use_llamaindex: bool = True
    allow_semantic_chunk_fallback: bool = False
    entity_min_confidence: float = DEFAULT_ENTITY_MIN_CONFIDENCE
    chunk_min_chars: int = DEFAULT_CHUNK_MIN_CHARS
    chunk_min_words: int = DEFAULT_CHUNK_MIN_WORDS
    list_chunk_min_words: int = DEFAULT_LIST_CHUNK_MIN_WORDS
    graph_backend: str = DEFAULT_GRAPH_BACKEND
    kuzu_db_path: str = DEFAULT_KUZU_DB_PATH
    graph_ingest_enabled: bool = True
    relation_min_confidence: float = DEFAULT_RELATION_MIN_CONFIDENCE
    retrieval_mode: str = DEFAULT_RETRIEVAL_MODE
    graph_retrieval_top_k: int = DEFAULT_GRAPH_RETRIEVAL_TOP_K
    graph_traversal_depth: int = DEFAULT_GRAPH_TRAVERSAL_DEPTH
    hybrid_vector_weight: float = DEFAULT_HYBRID_VECTOR_WEIGHT
    hybrid_graph_weight: float = DEFAULT_HYBRID_GRAPH_WEIGHT
    gitnexus_enabled: bool = False
    gitnexus_base_url: str = DEFAULT_GITNEXUS_BASE_URL


def load_settings() -> AppSettings:
    """Load application settings from environment variables."""

    return AppSettings(
        qdrant_url=os.getenv("QDRANT_URL", DEFAULT_QDRANT_URL).strip(),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        qdrant_collection=os.getenv("QDRANT_COLLECTION", DEFAULT_QDRANT_COLLECTION).strip(),
        guardrail_llm_enabled=env_bool("GUARDRAIL_LLM_ENABLED", True),
        llm_txt_path=os.getenv("LLM_TXT_PATH", DEFAULT_LLM_TXT_PATH).strip(),
        llm_provider=os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).strip().lower(),
        openai_model=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL).strip(),
        ollama_model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip(),
        qwen_model=os.getenv("QWEN_MODEL", DEFAULT_QWEN_MODEL).strip(),
        default_top_k=env_int("DEFAULT_TOP_K", DEFAULT_TOP_K),
        retrieval_min_score=env_float("RETRIEVAL_MIN_SCORE", DEFAULT_RETRIEVAL_MIN_SCORE),
        retrieval_rerank_enabled=env_bool("RETRIEVAL_RERANK_ENABLED", True),
        retrieval_rerank_top_k=env_int("RETRIEVAL_RERANK_TOP_K", DEFAULT_RETRIEVAL_RERANK_TOP_K),
        keyword_fallback_enabled=env_bool("KEYWORD_FALLBACK_ENABLED", True),
        keyword_fallback_min_score=env_float(
            "KEYWORD_FALLBACK_MIN_SCORE",
            DEFAULT_KEYWORD_FALLBACK_MIN_SCORE,
        ),
        keyword_fallback_candidate_limit=env_int(
            "KEYWORD_FALLBACK_CANDIDATE_LIMIT",
            DEFAULT_KEYWORD_FALLBACK_CANDIDATE_LIMIT,
        ),
        dataset_json_path=os.getenv("DATASET_JSON_PATH", DEFAULT_DATASET_JSON_PATH).strip(),
        dataset_csv_path=os.getenv("DATASET_CSV_PATH", DEFAULT_DATASET_CSV_PATH).strip(),
        dataset_primary_pdf_path=os.getenv(
            "DATASET_PRIMARY_PDF_PATH",
            DEFAULT_DATASET_PRIMARY_PDF_PATH,
        ).strip(),
        dataset_validation_pdf_path=os.getenv(
            "DATASET_VALIDATION_PDF_PATH",
            DEFAULT_DATASET_VALIDATION_PDF_PATH,
        ).strip(),
        chunking_strategy=os.getenv("CHUNKING_STRATEGY", DEFAULT_CHUNKING_STRATEGY).strip().lower(),
        semantic_chunk_max_chars=env_int(
            "SEMANTIC_CHUNK_MAX_CHARS",
            DEFAULT_SEMANTIC_CHUNK_MAX_CHARS,
        ),
        semantic_use_llamaindex=env_bool("SEMANTIC_USE_LLAMAINDEX", True),
        allow_semantic_chunk_fallback=env_bool("ALLOW_SEMANTIC_CHUNK_FALLBACK", False),
        entity_min_confidence=env_float("ENTITY_MIN_CONFIDENCE", DEFAULT_ENTITY_MIN_CONFIDENCE),
        chunk_min_chars=env_int("CHUNK_MIN_CHARS", DEFAULT_CHUNK_MIN_CHARS),
        chunk_min_words=env_int("CHUNK_MIN_WORDS", DEFAULT_CHUNK_MIN_WORDS),
        list_chunk_min_words=env_int("LIST_CHUNK_MIN_WORDS", DEFAULT_LIST_CHUNK_MIN_WORDS),
        graph_backend=os.getenv("GRAPH_BACKEND", DEFAULT_GRAPH_BACKEND).strip().lower(),
        kuzu_db_path=os.getenv("KUZU_DB_PATH", DEFAULT_KUZU_DB_PATH).strip(),
        graph_ingest_enabled=env_bool("GRAPH_INGEST_ENABLED", True),
        relation_min_confidence=env_float(
            "RELATION_MIN_CONFIDENCE",
            DEFAULT_RELATION_MIN_CONFIDENCE,
        ),
        retrieval_mode=os.getenv("RETRIEVAL_MODE", DEFAULT_RETRIEVAL_MODE).strip().lower(),
        graph_retrieval_top_k=env_int("GRAPH_RETRIEVAL_TOP_K", DEFAULT_GRAPH_RETRIEVAL_TOP_K),
        graph_traversal_depth=env_int("GRAPH_TRAVERSAL_DEPTH", DEFAULT_GRAPH_TRAVERSAL_DEPTH),
        hybrid_vector_weight=env_float("HYBRID_VECTOR_WEIGHT", DEFAULT_HYBRID_VECTOR_WEIGHT),
        hybrid_graph_weight=env_float("HYBRID_GRAPH_WEIGHT", DEFAULT_HYBRID_GRAPH_WEIGHT),
        gitnexus_enabled=env_bool("GITNEXUS_ENABLED", False),
        gitnexus_base_url=os.getenv("GITNEXUS_BASE_URL", DEFAULT_GITNEXUS_BASE_URL).strip(),
    )


def _read_system_prompt(path: str) -> str:
    """Read the base system prompt from disk, or return a safe default."""

    prompt_path = Path(path)
    if not prompt_path.exists():
        return DEFAULT_SYSTEM_PROMPT
    return prompt_path.read_text(encoding="utf-8").strip()


def validate_startup(
    command: str | None = None,
    settings: AppSettings | None = None,
) -> list[str]:
    """Validate startup configuration for the selected runtime command."""

    current = settings or load_settings()
    errors: list[str] = []

    if not current.qdrant_url:
        errors.append("QDRANT_URL is required.")
    if not current.qdrant_collection:
        errors.append("QDRANT_COLLECTION is required.")
    if current.default_top_k <= 0:
        errors.append("DEFAULT_TOP_K must be greater than 0.")
    if current.retrieval_min_score < 0:
        errors.append("RETRIEVAL_MIN_SCORE must be >= 0.")
    if current.retrieval_rerank_top_k <= 0:
        errors.append("RETRIEVAL_RERANK_TOP_K must be greater than 0.")
    if current.keyword_fallback_min_score < 0:
        errors.append("KEYWORD_FALLBACK_MIN_SCORE must be >= 0.")
    if current.keyword_fallback_candidate_limit <= 0:
        errors.append("KEYWORD_FALLBACK_CANDIDATE_LIMIT must be greater than 0.")
    if current.llm_provider not in SUPPORTED_LLM_PROVIDERS:
        providers = sorted(SUPPORTED_LLM_PROVIDERS)
        errors.append(f"LLM_PROVIDER must be one of {providers}, got '{current.llm_provider}'.")
    if current.chunking_strategy not in SUPPORTED_CHUNKING_STRATEGIES:
        errors.append(
            "CHUNKING_STRATEGY must be one of "
            f"{sorted(SUPPORTED_CHUNKING_STRATEGIES)}, got '{current.chunking_strategy}'."
        )
    if current.semantic_chunk_max_chars <= 0:
        errors.append("SEMANTIC_CHUNK_MAX_CHARS must be greater than 0.")
    if command in {INGEST_COMMAND} and current.chunking_strategy == "semantic" and not current.semantic_use_llamaindex:
        errors.append(
            "Semantic chunking is strict in this project. Set SEMANTIC_USE_LLAMAINDEX=true."
        )
    if command in {INGEST_COMMAND} and current.chunking_strategy == "semantic" and current.semantic_use_llamaindex:
        if not _llamaindex_semantic_available():
            errors.append(
                "Semantic chunking requires llama-index-core in runtime when "
                "SEMANTIC_USE_LLAMAINDEX=true. Install dependency before ingest."
            )
    if not 0 <= current.entity_min_confidence <= 1:
        errors.append("ENTITY_MIN_CONFIDENCE must be between 0 and 1.")
    if current.chunk_min_chars <= 0:
        errors.append("CHUNK_MIN_CHARS must be greater than 0.")
    if current.chunk_min_words <= 0:
        errors.append("CHUNK_MIN_WORDS must be greater than 0.")
    if current.list_chunk_min_words <= 0:
        errors.append("LIST_CHUNK_MIN_WORDS must be greater than 0.")
    if current.graph_backend not in SUPPORTED_GRAPH_BACKENDS:
        backends = sorted(SUPPORTED_GRAPH_BACKENDS)
        errors.append(f"GRAPH_BACKEND must be one of {backends}, got '{current.graph_backend}'.")
    if not current.kuzu_db_path:
        errors.append("KUZU_DB_PATH is required.")
    if not 0 <= current.relation_min_confidence <= 1:
        errors.append("RELATION_MIN_CONFIDENCE must be between 0 and 1.")
    if current.retrieval_mode not in SUPPORTED_RETRIEVAL_MODES:
        modes = sorted(SUPPORTED_RETRIEVAL_MODES)
        errors.append(f"RETRIEVAL_MODE must be one of {modes}, got '{current.retrieval_mode}'.")
    if current.graph_retrieval_top_k <= 0:
        errors.append("GRAPH_RETRIEVAL_TOP_K must be greater than 0.")
    if current.graph_traversal_depth <= 0:
        errors.append("GRAPH_TRAVERSAL_DEPTH must be greater than 0.")
    if current.hybrid_vector_weight < 0:
        errors.append("HYBRID_VECTOR_WEIGHT must be >= 0.")
    if current.hybrid_graph_weight < 0:
        errors.append("HYBRID_GRAPH_WEIGHT must be >= 0.")
    prompt_path = Path(current.llm_txt_path)
    if not prompt_path.exists():
        errors.append(f"Prompt file not found at '{current.llm_txt_path}'.")

    if command in {INGEST_COMMAND}:
        if not Path(current.dataset_json_path).exists():
            errors.append(f"Dataset JSON not found at '{current.dataset_json_path}'.")
        if not Path(current.dataset_csv_path).exists():
            errors.append(f"Dataset CSV not found at '{current.dataset_csv_path}'.")
        if not Path(current.dataset_primary_pdf_path).exists():
            errors.append(f"Primary dataset PDF not found at '{current.dataset_primary_pdf_path}'.")
        if not Path(current.dataset_validation_pdf_path).exists():
            errors.append(
                "Validation dataset PDF not found at "
                f"'{current.dataset_validation_pdf_path}'."
            )

    if command in {CHAT_COMMAND, EXTRACT_MARKDOWN_COMMAND} and current.llm_provider == DEFAULT_LLM_PROVIDER:
        if not os.getenv(OPENAI_API_KEY_ENV):
            errors.append(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai for chat or extract-markdown."
            )

    return errors


def _llamaindex_semantic_available() -> bool:
    """Return whether the semantic chunking dependency is installed."""

    return find_spec("llama_index.core.node_parser") is not None


def ensure_startup_valid(
    command: str | None = None,
    settings: AppSettings | None = None,
) -> None:
    """Raise a runtime error when startup validation finds configuration issues."""

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
