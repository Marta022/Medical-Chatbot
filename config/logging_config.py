from __future__ import annotations

import contextvars
import logging
import os
import sys
import uuid

_CORRELATION_ID = contextvars.ContextVar("correlation_id", default="-")
_CONFIGURED = False


class CorrelationIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = _CORRELATION_ID.get()
        return True


def set_correlation_id(value: str) -> None:
    _CORRELATION_ID.set(value)


def new_correlation_id() -> str:
    value = uuid.uuid4().hex
    _CORRELATION_ID.set(value)
    return value


def clear_correlation_id() -> None:
    _CORRELATION_ID.set("-")


def setup_logging(level: str | int | None = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    resolved_level = level or os.getenv("LOG_LEVEL", "INFO")
    if isinstance(resolved_level, str):
        resolved_level = getattr(logging, resolved_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(correlation_id)s | %(message)s"
    )
    handler.setFormatter(formatter)
    handler.addFilter(CorrelationIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(resolved_level)
    root.addHandler(handler)

    _CONFIGURED = True


def add_file_handler(path: str) -> None:
    """Add a file handler to the root logger so all subsequent log messages are also written to *path*."""
    import pathlib

    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(path, mode="w", encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(correlation_id)s | %(message)s"
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(CorrelationIdFilter())
    logging.getLogger().addHandler(file_handler)
