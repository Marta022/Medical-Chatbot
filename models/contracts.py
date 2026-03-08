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
    provenance: str = "vector"

    def titles(self) -> list[str]:
        return [hit.title for hit in self.hits]

    def context_lines(self, with_score: bool = True) -> list[str]:
        if with_score:
            return [f"{hit.text} ({hit.score:.4f})" for hit in self.hits]
        return [hit.text for hit in self.hits]

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": [hit.to_dict() for hit in self.hits],
            "provenance": self.provenance,
        }

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
        return cls(hits=hits, provenance=str(value.get("provenance", "vector")))

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


@dataclass
class TocExtractionConfig:
    pdf_path: str
    toc_page_index: int = 1
    expected_columns: int = 2
    page_offset: int = 0
    min_native_text_chars: int = 120
    use_pp_structure_fallback: bool = True
    ignored_terms: tuple[str, ...] = ("contents", "cuprins")

    def __post_init__(self) -> None:
        if not self.pdf_path.strip():
            raise ValueError("pdf_path must be a non-empty string")
        if self.toc_page_index < 0:
            raise ValueError("toc_page_index must be >= 0")
        if self.expected_columns <= 0:
            raise ValueError("expected_columns must be > 0")
        if self.min_native_text_chars <= 0:
            raise ValueError("min_native_text_chars must be > 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "pdf_path": self.pdf_path,
            "toc_page_index": self.toc_page_index,
            "expected_columns": self.expected_columns,
            "page_offset": self.page_offset,
            "min_native_text_chars": self.min_native_text_chars,
            "use_pp_structure_fallback": self.use_pp_structure_fallback,
            "ignored_terms": list(self.ignored_terms),
        }


@dataclass
class TocEntry:
    chapter: str
    subchapter: str | None
    start_page: int
    end_page: int
    original_toc_text: str

    def __post_init__(self) -> None:
        if not self.chapter.strip():
            raise ValueError("chapter must be a non-empty string")
        if self.start_page <= 0:
            raise ValueError("start_page must be > 0")
        if self.end_page < self.start_page:
            raise ValueError("end_page must be >= start_page")
        if not self.original_toc_text.strip():
            raise ValueError("original_toc_text must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter": self.chapter,
            "subchapter": self.subchapter,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "original_toc_text": self.original_toc_text,
        }


@dataclass
class TocSectionContent:
    chapter: str
    subchapter: str | None
    start_page: int
    end_page: int
    original_toc_text: str
    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise ValueError("text must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter": self.chapter,
            "subchapter": self.subchapter,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "original_toc_text": self.original_toc_text,
            "text": self.text,
        }


@dataclass
class TocAgentEntry:
    chapter: str
    subchapter: str | None
    printed_start_page: int
    original_toc_text: str

    def __post_init__(self) -> None:
        if not self.chapter.strip():
            raise ValueError("chapter must be a non-empty string")
        if self.printed_start_page <= 0:
            raise ValueError("printed_start_page must be > 0")
        if not self.original_toc_text.strip():
            raise ValueError("original_toc_text must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter": self.chapter,
            "subchapter": self.subchapter,
            "printed_start_page": self.printed_start_page,
            "original_toc_text": self.original_toc_text,
        }


@dataclass
class TocPageValidationConfig:
    expected_page_offset: int = 0
    search_window: int = 2
    require_title_hint: bool = False

    def __post_init__(self) -> None:
        if self.search_window < 0:
            raise ValueError("search_window must be >= 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected_page_offset": self.expected_page_offset,
            "search_window": self.search_window,
            "require_title_hint": self.require_title_hint,
        }


@dataclass
class TocValidatedEntry:
    chapter: str
    subchapter: str | None
    printed_start_page: int
    validated_start_page: int
    original_toc_text: str
    page_validation_status: str = "UNVERIFIED"
    page_validation_method: str = "none"
    matched_page_marker: str | None = None
    matched_title_hint: str | None = None

    def __post_init__(self) -> None:
        if not self.chapter.strip():
            raise ValueError("chapter must be a non-empty string")
        if self.printed_start_page <= 0:
            raise ValueError("printed_start_page must be > 0")
        if self.validated_start_page <= 0:
            raise ValueError("validated_start_page must be > 0")
        if not self.original_toc_text.strip():
            raise ValueError("original_toc_text must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter": self.chapter,
            "subchapter": self.subchapter,
            "printed_start_page": self.printed_start_page,
            "validated_start_page": self.validated_start_page,
            "original_toc_text": self.original_toc_text,
            "page_validation_status": self.page_validation_status,
            "page_validation_method": self.page_validation_method,
            "matched_page_marker": self.matched_page_marker,
            "matched_title_hint": self.matched_title_hint,
        }


@dataclass
class TocValidationResult:
    entries: list[TocValidatedEntry]
    config: TocPageValidationConfig

    def to_dict(self) -> dict[str, Any]:
        return {
            "entries": [entry.to_dict() for entry in self.entries],
            "config": self.config.to_dict(),
        }


@dataclass
class TocValidatedSectionContent:
    chapter: str
    subchapter: str | None
    printed_start_page: int
    validated_start_page: int
    validated_end_page: int
    original_toc_text: str
    page_validation_status: str
    page_validation_method: str
    text: str
    matched_page_marker: str | None = None
    matched_title_hint: str | None = None

    def __post_init__(self) -> None:
        if not self.chapter.strip():
            raise ValueError("chapter must be a non-empty string")
        if self.printed_start_page <= 0:
            raise ValueError("printed_start_page must be > 0")
        if self.validated_start_page <= 0:
            raise ValueError("validated_start_page must be > 0")
        if self.validated_end_page < self.validated_start_page:
            raise ValueError("validated_end_page must be >= validated_start_page")
        if not self.original_toc_text.strip():
            raise ValueError("original_toc_text must be a non-empty string")
        if not self.text.strip():
            raise ValueError("text must be a non-empty string")

    def to_dict(self) -> dict[str, Any]:
        return {
            "chapter": self.chapter,
            "subchapter": self.subchapter,
            "printed_start_page": self.printed_start_page,
            "validated_start_page": self.validated_start_page,
            "validated_end_page": self.validated_end_page,
            "original_toc_text": self.original_toc_text,
            "page_validation_status": self.page_validation_status,
            "page_validation_method": self.page_validation_method,
            "matched_page_marker": self.matched_page_marker,
            "matched_title_hint": self.matched_title_hint,
            "text": self.text,
        }
