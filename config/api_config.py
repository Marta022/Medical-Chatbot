"""API-specific runtime configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

from config.common import env_bool, env_int

DEFAULT_API_MAX_QUERY_CHARS = 2000
DEFAULT_API_MAX_MESSAGES = 32
DEFAULT_API_MAX_TOP_K = 10


@dataclass(frozen=True)
class ApiSettings:
    """Configuration flags and limits for the HTTP API surface."""

    api_enabled: bool = True
    require_api_key: bool = False
    api_key: str | None = None
    max_query_chars: int = DEFAULT_API_MAX_QUERY_CHARS
    max_messages: int = DEFAULT_API_MAX_MESSAGES
    max_top_k: int = DEFAULT_API_MAX_TOP_K


def load_api_settings() -> ApiSettings:
    """Load API settings from environment variables."""

    return ApiSettings(
        api_enabled=env_bool("API_ENABLED", True),
        require_api_key=env_bool("API_REQUIRE_KEY", False),
        api_key=os.getenv("API_KEY"),
        max_query_chars=env_int("API_MAX_QUERY_CHARS", DEFAULT_API_MAX_QUERY_CHARS),
        max_messages=env_int("API_MAX_MESSAGES", DEFAULT_API_MAX_MESSAGES),
        max_top_k=env_int("API_MAX_TOP_K", DEFAULT_API_MAX_TOP_K),
    )


API_SETTINGS = load_api_settings()
