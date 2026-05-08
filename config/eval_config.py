"""Evaluator retry and scoring configuration."""

from __future__ import annotations

from dataclasses import dataclass
from os import getenv

from config.common import env_bool, env_float, env_int

DEFAULT_EVAL_PASS_SCORE = 0.7
DEFAULT_EVAL_MAX_RETRIES = 2
DEFAULT_PROVIDER_FALLBACK_ORDER = ("openai", "ollama")
DEFAULT_EVAL_BORDERLINE_LOW = 0.45
DEFAULT_EVAL_BORDERLINE_HIGH = 0.65
DEFAULT_EVAL_USE_LLM_JUDGE = False
DEFAULT_EVAL_SAFE_MIN_LENGTH = 80


@dataclass(frozen=True)
class EvalConfig:
    """Configuration for evaluator acceptance and retry behavior."""

    pass_score: float = DEFAULT_EVAL_PASS_SCORE
    max_retries: int = DEFAULT_EVAL_MAX_RETRIES
    provider_fallback_order: tuple[str, ...] = DEFAULT_PROVIDER_FALLBACK_ORDER
    borderline_low: float = DEFAULT_EVAL_BORDERLINE_LOW
    borderline_high: float = DEFAULT_EVAL_BORDERLINE_HIGH
    use_llm_judge: bool = DEFAULT_EVAL_USE_LLM_JUDGE
    safe_min_length: int = DEFAULT_EVAL_SAFE_MIN_LENGTH


def load_eval_config() -> EvalConfig:
    """Load evaluator configuration from environment variables."""

    fallback_raw = getenv("EVAL_PROVIDER_FALLBACK_ORDER", "")
    fallback_order = (
        tuple(item.strip().lower() for item in fallback_raw.split(",") if item.strip())
        or DEFAULT_PROVIDER_FALLBACK_ORDER
    )
    return EvalConfig(
        pass_score=env_float("EVAL_PASS_SCORE", DEFAULT_EVAL_PASS_SCORE),
        max_retries=env_int("EVAL_MAX_RETRIES", DEFAULT_EVAL_MAX_RETRIES),
        provider_fallback_order=fallback_order,
        borderline_low=env_float("EVAL_BORDERLINE_LOW", DEFAULT_EVAL_BORDERLINE_LOW),
        borderline_high=env_float("EVAL_BORDERLINE_HIGH", DEFAULT_EVAL_BORDERLINE_HIGH),
        use_llm_judge=env_bool("EVAL_USE_LLM_JUDGE", DEFAULT_EVAL_USE_LLM_JUDGE),
        safe_min_length=env_int("EVAL_SAFE_MIN_LENGTH", DEFAULT_EVAL_SAFE_MIN_LENGTH),
    )


EVAL_CONFIG = load_eval_config()
