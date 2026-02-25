from __future__ import annotations

import os
from dataclasses import dataclass


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
class ApiSettings:
    api_enabled: bool = True
    require_api_key: bool = False
    api_key: str | None = None
    max_query_chars: int = 2000
    max_messages: int = 32
    max_top_k: int = 10


def load_api_settings() -> ApiSettings:
    return ApiSettings(
        api_enabled=_env_bool("API_ENABLED", True),
        require_api_key=_env_bool("API_REQUIRE_KEY", False),
        api_key=os.getenv("API_KEY"),
        max_query_chars=_env_int("API_MAX_QUERY_CHARS", 2000),
        max_messages=_env_int("API_MAX_MESSAGES", 32),
        max_top_k=_env_int("API_MAX_TOP_K", 10),
    )


API_SETTINGS = load_api_settings()
