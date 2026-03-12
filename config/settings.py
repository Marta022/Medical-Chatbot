from __future__ import annotations

import os
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

SUPPORTED_LLM_PROVIDERS = {"openai", "ollama", "qwen3.5"}
SUPPORTED_CHUNKING_STRATEGIES = {"section", "sentence", "window", "semantic"}
SUPPORTED_GRAPH_BACKENDS = {"kuzu"}
SUPPORTED_RETRIEVAL_MODES = {"vector", "hybrid"}


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
    openai_model: str = "gpt-4o-mini"
    ollama_model: str = "gemma2:2b"
    qwen_model: str = "qwen3.5"
    default_top_k: int = 3
    retrieval_min_score: float = 0.2
    retrieval_rerank_enabled: bool = True
    retrieval_rerank_top_k: int = 12
    keyword_fallback_enabled: bool = True
    keyword_fallback_min_score: float = 0.18
    keyword_fallback_candidate_limit: int = 1500
    dataset_json_path: str = "data/dataset/disease_database.json"
    dataset_csv_path: str = "data/dataset/dataset_sheet1.csv"
    dataset_primary_pdf_path: str = "data/dataset/DORIN-CURS_SEM2_searchable.pdf"
    dataset_validation_pdf_path: str = (
        "data/dataset/DORIN_GENERALA_CARDIOVASCULARA-RESPIRATORIE-DISESTIVA.CV01.pdf"
    )
    chunking_strategy: str = "semantic"
    semantic_chunk_max_chars: int = 700
    semantic_use_llamaindex: bool = True
    allow_semantic_chunk_fallback: bool = False
    allow_fallback_embeddings: bool = False
    entity_min_confidence: float = 0.65
    chunk_min_chars: int = 40
    chunk_min_words: int = 8
    list_chunk_min_words: int = 2
    graph_backend: str = "kuzu"
    kuzu_db_path: str = "knowledge/graph/kuzu_storage"
    graph_ingest_enabled: bool = True
    relation_min_confidence: float = 0.7
    retrieval_mode: str = "vector"
    graph_retrieval_top_k: int = 3
    graph_traversal_depth: int = 1
    hybrid_vector_weight: float = 1.0
    hybrid_graph_weight: float = 0.9
    gitnexus_enabled: bool = False
    gitnexus_base_url: str = "http://localhost:8088"


def load_settings() -> AppSettings:
    return AppSettings(
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333").strip(),
        qdrant_api_key=os.getenv("QDRANT_API_KEY"),
        qdrant_collection=os.getenv("QDRANT_COLLECTION", "medical_docs").strip(),
        guardrail_llm_enabled=_env_bool("GUARDRAIL_LLM_ENABLED", True),
        llm_txt_path=os.getenv("LLM_TXT_PATH", "llm.txt").strip(),
        llm_provider=os.getenv("LLM_PROVIDER", "openai").strip().lower(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip(),
        ollama_model=os.getenv("OLLAMA_MODEL", "gemma2:2b").strip(),
        qwen_model=os.getenv("QWEN_MODEL", "qwen3.5").strip(),
        default_top_k=_env_int("DEFAULT_TOP_K", 3),
        retrieval_min_score=float(os.getenv("RETRIEVAL_MIN_SCORE", "0.2").strip()),
        retrieval_rerank_enabled=_env_bool("RETRIEVAL_RERANK_ENABLED", True),
        retrieval_rerank_top_k=_env_int("RETRIEVAL_RERANK_TOP_K", 12),
        keyword_fallback_enabled=_env_bool("KEYWORD_FALLBACK_ENABLED", True),
        keyword_fallback_min_score=float(os.getenv("KEYWORD_FALLBACK_MIN_SCORE", "0.18").strip()),
        keyword_fallback_candidate_limit=_env_int("KEYWORD_FALLBACK_CANDIDATE_LIMIT", 1500),
        dataset_json_path=os.getenv(
            "DATASET_JSON_PATH",
            "data/dataset/disease_database.json",
        ).strip(),
        dataset_csv_path=os.getenv(
            "DATASET_CSV_PATH",
            "data/dataset/dataset_sheet1.csv",
        ).strip(),
        dataset_primary_pdf_path=os.getenv(
            "DATASET_PRIMARY_PDF_PATH",
            "data/dataset/DORIN-CURS_SEM2_searchable.pdf",
        ).strip(),
        dataset_validation_pdf_path=os.getenv(
            "DATASET_VALIDATION_PDF_PATH",
            "data/dataset/DORIN_GENERALA_CARDIOVASCULARA-RESPIRATORIE-DISESTIVA.CV01.pdf",
        ).strip(),
        chunking_strategy=os.getenv("CHUNKING_STRATEGY", "semantic").strip().lower(),
        semantic_chunk_max_chars=_env_int("SEMANTIC_CHUNK_MAX_CHARS", 700),
        semantic_use_llamaindex=_env_bool("SEMANTIC_USE_LLAMAINDEX", True),
        allow_semantic_chunk_fallback=_env_bool("ALLOW_SEMANTIC_CHUNK_FALLBACK", False),
        allow_fallback_embeddings=_env_bool("ALLOW_FALLBACK_EMBEDDINGS", False),
        entity_min_confidence=float(os.getenv("ENTITY_MIN_CONFIDENCE", "0.65").strip()),
        chunk_min_chars=_env_int("CHUNK_MIN_CHARS", 40),
        chunk_min_words=_env_int("CHUNK_MIN_WORDS", 8),
        list_chunk_min_words=_env_int("LIST_CHUNK_MIN_WORDS", 2),
        graph_backend=os.getenv("GRAPH_BACKEND", "kuzu").strip().lower(),
        kuzu_db_path=os.getenv("KUZU_DB_PATH", "knowledge/graph/kuzu_storage").strip(),
        graph_ingest_enabled=_env_bool("GRAPH_INGEST_ENABLED", True),
        relation_min_confidence=float(os.getenv("RELATION_MIN_CONFIDENCE", "0.7").strip()),
        retrieval_mode=os.getenv("RETRIEVAL_MODE", "vector").strip().lower(),
        graph_retrieval_top_k=_env_int("GRAPH_RETRIEVAL_TOP_K", 3),
        graph_traversal_depth=_env_int("GRAPH_TRAVERSAL_DEPTH", 1),
        hybrid_vector_weight=float(os.getenv("HYBRID_VECTOR_WEIGHT", "1.0").strip()),
        hybrid_graph_weight=float(os.getenv("HYBRID_GRAPH_WEIGHT", "0.9").strip()),
        gitnexus_enabled=_env_bool("GITNEXUS_ENABLED", False),
        gitnexus_base_url=os.getenv("GITNEXUS_BASE_URL", "http://localhost:8088").strip(),
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
        errors.append(
            f"LLM_PROVIDER must be one of {providers}, got '{current.llm_provider}'."
        )
    if current.chunking_strategy not in SUPPORTED_CHUNKING_STRATEGIES:
        errors.append(
            "CHUNKING_STRATEGY must be one of "
            f"{sorted(SUPPORTED_CHUNKING_STRATEGIES)}, got '{current.chunking_strategy}'."
        )
    if current.semantic_chunk_max_chars <= 0:
        errors.append("SEMANTIC_CHUNK_MAX_CHARS must be greater than 0.")
    if command in {"ingest"} and current.chunking_strategy == "semantic" and not current.semantic_use_llamaindex:
        errors.append(
            "Semantic chunking is strict in this project. Set SEMANTIC_USE_LLAMAINDEX=true."
        )
    if (
        command in {"ingest"}
        and current.chunking_strategy == "semantic"
        and current.semantic_use_llamaindex
    ):
        if not _llamaindex_semantic_available():
            errors.append(
                "Semantic chunking requires llama-index-core in runtime when "
                "SEMANTIC_USE_LLAMAINDEX=true. Install dependency before ingest."
            )
    if command in {"chat", "ingest"} and not current.allow_fallback_embeddings:
        if _using_fallback_embeddings():
            errors.append(
                "Embedding backend is running in deterministic fallback mode. "
                "Provide cached model artifacts or set ALLOW_FALLBACK_EMBEDDINGS=true."
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
        errors.append(
            f"GRAPH_BACKEND must be one of {backends}, got '{current.graph_backend}'."
        )
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
    if current.gitnexus_enabled and not current.gitnexus_base_url:
        errors.append("GITNEXUS_BASE_URL is required when GITNEXUS_ENABLED=true.")

    prompt_path = Path(current.llm_txt_path)
    if not prompt_path.exists():
        errors.append(f"Prompt file not found at '{current.llm_txt_path}'.")

    if command in {"ingest"}:
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

    if command in {"chat", "extract-markdown"} and current.llm_provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            errors.append(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai for chat or extract-markdown."
            )

    return errors


def _llamaindex_semantic_available() -> bool:
    return find_spec("llama_index.core.node_parser") is not None


def _using_fallback_embeddings() -> bool:
    try:
        from rag.retrieval.embeddings import embed_query, using_fallback_embeddings

        embed_query("startup-check")
        return using_fallback_embeddings()
    except Exception:
        return True


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
