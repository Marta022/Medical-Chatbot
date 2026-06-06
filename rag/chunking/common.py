"""Shared text-structure helpers for chunking and document parsing."""

from __future__ import annotations

import re

NUMBERED_ITEM_PATTERN = re.compile(r"^\s*\d+[\.\)]\s+\S+")
BULLET_ITEM_PATTERN = re.compile(r"^\s*[-*•◦▪▫‣∙◆◇■□✦✧]\s+\S+")
MARKDOWN_HEADING_PATTERN = re.compile(r"^\s*(#{1,3})\s+(.+?)\s*$")
WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_line(text: str) -> str:
    """Normalize whitespace inside one extracted line."""

    return WHITESPACE_PATTERN.sub(" ", text).strip()


def is_numbered_item(line: str) -> bool:
    """Return whether a line starts with a numbered-list marker."""

    return bool(NUMBERED_ITEM_PATTERN.match(line.strip()))


def is_bullet_item(line: str) -> bool:
    """Return whether a line starts with a bullet-list marker."""

    return bool(BULLET_ITEM_PATTERN.match(line.strip()))


def is_markdown_heading(line: str) -> bool:
    """Return whether a line matches a markdown heading pattern."""

    return bool(MARKDOWN_HEADING_PATTERN.match(line.strip()))
