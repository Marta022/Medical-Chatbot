"""Shared environment parsing helpers for configuration modules."""

from __future__ import annotations

import os

TRUTHY_ENV_VALUES = {"1", "true", "yes", "on"}


def env_bool(name: str, default: bool) -> bool:
    """Read a boolean environment variable with a default fallback."""

    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in TRUTHY_ENV_VALUES


def env_int(name: str, default: int) -> int:
    """Read an integer environment variable with a default fallback."""

    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def env_float(name: str, default: float) -> float:
    """Read a float environment variable with a default fallback."""

    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw.strip())
    except ValueError:
        return default
