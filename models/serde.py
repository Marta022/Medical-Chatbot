from __future__ import annotations

"""Serialization helpers for typed model contracts."""

import json
from dataclasses import asdict, is_dataclass
from typing import Any, TypeVar

from models.contracts import (
    EvaluatorResult,
    GuardrailResult,
    LLMResponse,
    QueryRequest,
    RetrievalResult,
)

T = TypeVar("T")


def serialize_to_json_compatible(value: Any) -> Any:
    """Recursively convert dataclass-backed values to JSON-compatible structures."""

    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [serialize_to_json_compatible(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_to_json_compatible(item) for key, item in value.items()}
    return value


def serialize_to_json(value: Any) -> str:
    """Serialize supported values to JSON with unicode preserved."""

    payload = serialize_to_json_compatible(value)
    return json.dumps(payload, ensure_ascii=False)


def query_request_from_dict(value: dict[str, Any]) -> QueryRequest:
    """Deserialize QueryRequest from dictionary."""

    return QueryRequest.from_dict(value)


def guardrail_result_from_dict(value: dict[str, Any]) -> GuardrailResult:
    """Deserialize GuardrailResult from dictionary."""

    return GuardrailResult.from_dict(value)


def retrieval_result_from_dict(value: dict[str, Any]) -> RetrievalResult:
    """Deserialize RetrievalResult from dictionary."""

    return RetrievalResult.from_dict(value)


def llm_response_from_dict(value: dict[str, Any]) -> LLMResponse:
    """Deserialize LLMResponse from dictionary."""

    return LLMResponse(
        content=str(value.get("content", "")),
        provider=str(value.get("provider", "")),
        model=value.get("model"),
    )


def evaluator_result_from_dict(value: dict[str, Any]) -> EvaluatorResult:
    """Deserialize EvaluatorResult from dictionary."""

    return EvaluatorResult(
        passed=bool(value.get("passed", False)),
        score=float(value.get("score", 0.0)),
        reasons=[str(item) for item in value.get("reasons", [])],
        retry_recommended=bool(value.get("retry_recommended", False)),
        failure_types=[str(item) for item in value.get("failure_types", [])],
        adaptive_prompt=(
            str(value.get("adaptive_prompt")) if value.get("adaptive_prompt") is not None else None
        ),
        retry_strategy=str(value.get("retry_strategy", "adjust_prompt")),
        judge_used=bool(value.get("judge_used", False)),
    )
