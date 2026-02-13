from __future__ import annotations

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
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [serialize_to_json_compatible(item) for item in value]
    if isinstance(value, dict):
        return {key: serialize_to_json_compatible(item) for key, item in value.items()}
    return value


def serialize_to_json(value: Any) -> str:
    payload = serialize_to_json_compatible(value)
    return json.dumps(payload, ensure_ascii=False)


def query_request_from_dict(value: dict[str, Any]) -> QueryRequest:
    return QueryRequest.from_dict(value)


def guardrail_result_from_dict(value: dict[str, Any]) -> GuardrailResult:
    return GuardrailResult.from_dict(value)


def retrieval_result_from_dict(value: dict[str, Any]) -> RetrievalResult:
    return RetrievalResult.from_dict(value)


def llm_response_from_dict(value: dict[str, Any]) -> LLMResponse:
    return LLMResponse(
        content=str(value.get("content", "")),
        provider=str(value.get("provider", "")),
        model=value.get("model"),
    )


def evaluator_result_from_dict(value: dict[str, Any]) -> EvaluatorResult:
    return EvaluatorResult(
        passed=bool(value.get("passed", False)),
        score=float(value.get("score", 0.0)),
        reasons=[str(item) for item in value.get("reasons", [])],
        retry_recommended=bool(value.get("retry_recommended", False)),
    )

