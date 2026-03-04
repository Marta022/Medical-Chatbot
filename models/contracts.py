from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueryRequest:
    query: str
    top_k: int = 3
    language: str = "ro"
    filters: dict[str, str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.query, str) or not self.query.strip():
            raise ValueError("query must be a non-empty string")
        if self.top_k <= 0:
            raise ValueError("top_k must be greater than 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "top_k": self.top_k,
            "language": self.language,
            "filters": self.filters,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> QueryRequest:
        return cls(
            query=str(value.get("query", "")),
            top_k=int(value.get("top_k", 3)),
            language=str(value.get("language", "ro")),
            filters=value.get("filters"),
        )


@dataclass
class GuardrailResult:
    is_emergency: bool = False
    is_unsafe: bool = False
    is_valid: bool = True
    message: str | None = None
    reason_code: str = "SAFE"
    confidence: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_emergency": self.is_emergency,
            "is_unsafe": self.is_unsafe,
            "is_valid": self.is_valid,
            "message": self.message,
            "reason_code": self.reason_code,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> GuardrailResult:
        return cls(
            is_emergency=bool(value.get("is_emergency", False)),
            is_unsafe=bool(value.get("is_unsafe", False)),
            is_valid=bool(value.get("is_valid", True)),
            message=value.get("message"),
            reason_code=str(value.get("reason_code", "SAFE")),
            confidence=float(value.get("confidence", 1.0)),
        )


@dataclass
class RetrievalHit:
    title: str
    text: str
    score: float
    source: str = "unknown"
    source_file: str | None = None
    page: int | None = None
    section: str | None = None
    chunk_id: str | None = None

    def __post_init__(self) -> None:
        self.title = self.title.strip()
        self.text = self.text.strip()

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "text": self.text,
            "score": self.score,
            "source": self.source,
            "source_file": self.source_file,
            "page": self.page,
            "section": self.section,
            "chunk_id": self.chunk_id,
        }


@dataclass
class RetrievalResult:
    hits: list[RetrievalHit] = field(default_factory=list)

    def titles(self) -> list[str]:
        return [hit.title for hit in self.hits]

    def context_lines(self, with_score: bool = True) -> list[str]:
        if with_score:
            return [f"{hit.text} ({hit.score:.4f})" for hit in self.hits]
        return [hit.text for hit in self.hits]

    def to_dict(self) -> dict[str, Any]:
        return {"hits": [hit.to_dict() for hit in self.hits]}

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> RetrievalResult:
        raw_hits = value.get("hits", [])
        hits = [
            RetrievalHit(
                title=str(item.get("title", "")),
                text=str(item.get("text", "")),
                score=float(item.get("score", 0.0)),
                source=str(item.get("source", "unknown")),
                source_file=(
                    str(item.get("source_file"))
                    if item.get("source_file") is not None
                    else None
                ),
                page=int(item.get("page")) if item.get("page") is not None else None,
                section=str(item.get("section")) if item.get("section") is not None else None,
                chunk_id=str(item.get("chunk_id")) if item.get("chunk_id") is not None else None,
            )
            for item in raw_hits
        ]
        return cls(hits=hits)

    def max_score(self) -> float:
        if not self.hits:
            return 0.0
        return max(hit.score for hit in self.hits)


@dataclass
class LLMMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class LLMRequest:
    system_prompt: str
    user_message: str
    context_block: str = ""
    temperature: float = 0.0
    provider: str | None = None

    def messages(self) -> list[dict[str, str]]:
        user_payload = self.user_message
        if self.context_block:
            user_payload = f"{self.user_message}\n\n{self.context_block}"
        return [
            LLMMessage(role="system", content=self.system_prompt).to_dict(),
            LLMMessage(role="user", content=user_payload).to_dict(),
        ]


@dataclass
class LLMResponse:
    content: str
    provider: str
    model: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {"content": self.content, "provider": self.provider, "model": self.model}


@dataclass
class EvaluatorResult:
    passed: bool
    score: float
    reasons: list[str] = field(default_factory=list)
    retry_recommended: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "reasons": self.reasons,
            "retry_recommended": self.retry_recommended,
        }


@dataclass
class OrchestratorResponse:
    response: str | None
    provider: str | None
    model: str | None
    retries: int
    guardrail: GuardrailResult
    evaluator: EvaluatorResult | None
    retrieval: RetrievalResult | None
    context_lines: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "response": self.response,
            "provider": self.provider,
            "model": self.model,
            "retries": self.retries,
            "guardrail": self.guardrail.to_dict(),
            "evaluator": self.evaluator.to_dict() if self.evaluator else None,
            "retrieval": self.retrieval.to_dict() if self.retrieval else None,
            "context_lines": self.context_lines,
        }


@dataclass
class MedicalItem:
    title: str
    description: str
    source: str
    category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "category": self.category,
        }


@dataclass
class PdfStructuredChunk:
    source_file: str
    page: int
    chapter: str
    section: str
    chunk_id: str
    text: str
    is_list: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "page": self.page,
            "chapter": self.chapter,
            "section": self.section,
            "chunk_id": self.chunk_id,
            "text": self.text,
            "is_list": self.is_list,
        }


@dataclass
class MedicalEntity:
    entity_type: str
    mention_text: str
    canonical_form: str
    confidence: float
    source_file: str
    page: int
    chunk_id: str
    chapter: str = "unknown"
    section: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_type": self.entity_type,
            "mention_text": self.mention_text,
            "canonical_form": self.canonical_form,
            "confidence": self.confidence,
            "source_file": self.source_file,
            "page": self.page,
            "chunk_id": self.chunk_id,
            "chapter": self.chapter,
            "section": self.section,
        }


@dataclass
class MedicalRelation:
    predicate: str
    source_entity_id: str
    source_entity_type: str
    source_canonical_form: str
    target_entity_id: str
    target_entity_type: str
    target_canonical_form: str
    confidence: float
    source_file: str
    page: int
    chunk_id: str
    chapter: str = "unknown"
    section: str = "unknown"
    evidence_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "predicate": self.predicate,
            "source_entity_id": self.source_entity_id,
            "source_entity_type": self.source_entity_type,
            "source_canonical_form": self.source_canonical_form,
            "target_entity_id": self.target_entity_id,
            "target_entity_type": self.target_entity_type,
            "target_canonical_form": self.target_canonical_form,
            "confidence": self.confidence,
            "source_file": self.source_file,
            "page": self.page,
            "chunk_id": self.chunk_id,
            "chapter": self.chapter,
            "section": self.section,
            "evidence_text": self.evidence_text,
        }
