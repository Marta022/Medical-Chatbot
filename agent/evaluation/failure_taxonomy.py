from __future__ import annotations

"""Failure taxonomy for evaluator rejection reasons."""

from enum import Enum


class FailureType(str, Enum):
    """Structured evaluator failure types used for adaptive retries."""

    EMPTY = "empty"
    TOO_SHORT = "too_short"
    CONTEXT_IGNORED = "context_ignored"
    HALLUCINATION_RISK = "hallucination_risk"
    REFUSED_WITH_CONTEXT = "refused_with_context"
    UNSAFE_ADVICE = "unsafe_advice"
    OFF_TOPIC = "off_topic"
    INCOMPLETE = "incomplete"
    BORDERLINE = "borderline"
    UNKNOWN = "unknown"
