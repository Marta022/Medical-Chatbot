"""Evaluator retry and scoring configuration."""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_EVAL_PASS_SCORE = 0.7
DEFAULT_EVAL_MAX_RETRIES = 2
DEFAULT_PROVIDER_FALLBACK_ORDER = ("openai", "ollama")


@dataclass(frozen=True)
class EvalConfig:
    """Configuration for evaluator acceptance and retry behavior."""

    pass_score: float = DEFAULT_EVAL_PASS_SCORE
    max_retries: int = DEFAULT_EVAL_MAX_RETRIES
    provider_fallback_order: tuple[str, ...] = DEFAULT_PROVIDER_FALLBACK_ORDER


EVAL_CONFIG = EvalConfig()
