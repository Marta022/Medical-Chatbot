from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvalConfig:
    pass_score: float = 0.7
    max_retries: int = 2
    provider_fallback_order: tuple[str, ...] = ("openai", "ollama")


EVAL_CONFIG = EvalConfig()
