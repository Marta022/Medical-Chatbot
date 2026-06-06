"""Logging setup with correlation ID propagation."""

from __future__ import annotations

import contextvars
import logging
import os
import sys
import uuid
from pathlib import Path

DEFAULT_CORRELATION_ID = "-"
DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(correlation_id)s | %(message)s"
_CORRELATION_ID = contextvars.ContextVar("correlation_id", default=DEFAULT_CORRELATION_ID)
_CONFIGURED = False


class CorrelationIdFilter(logging.Filter):
    """Inject the active correlation ID into every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = _CORRELATION_ID.get()
        return True


def set_correlation_id(value: str) -> None:
    """Set the correlation ID for the current context."""

    _CORRELATION_ID.set(value)


def new_correlation_id() -> str:
    """Generate and store a fresh correlation ID for the current context."""

    value = uuid.uuid4().hex
    _CORRELATION_ID.set(value)
    return value


def clear_correlation_id() -> None:
    """Reset the current correlation ID to the default placeholder."""

    _CORRELATION_ID.set(DEFAULT_CORRELATION_ID)


def setup_logging(level: str | int | None = None) -> None:
    """Configure root logging once for console output with correlation IDs."""

    global _CONFIGURED
    if _CONFIGURED:
        return

    resolved_level = level or os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)
    if isinstance(resolved_level, str):
        resolved_level = getattr(logging, resolved_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(resolved_level)
    root.addHandler(handler)

    _CONFIGURED = True


def add_file_handler(path: str) -> None:
    """Add a root file handler so logs are also written to the given path."""

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(path, mode="w", encoding="utf-8")
    formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(CorrelationIdFilter())
    logging.getLogger().addHandler(file_handler)
