from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
from pathlib import Path

from models import MedicalItem
from models.contracts import PdfStructuredChunk
from rag.chunking.strategies import chunk_structured_chunks

logger = logging.getLogger(__name__)

_CHAPTER_PATTERN = re.compile(r"^\s*(capitol(?:ul)?\.?\s*\d+|chapter\s+\d+)\b", re.IGNORECASE)
_SECTION_PATTERN = re.compile(r"^\s*\d+(?:\.\d+){1,}\s+\S+")
_NUMBERED_ITEM_PATTERN = re.compile(r"^\s*\d+[\.\)]\s+\S+")
_BULLET_ITEM_PATTERN = re.compile(r"^\s*[-*•]\s+\S+")
_PDF_LITERAL_PATTERN = re.compile(r"\((?P<literal>(?:\\.|[^\\)])*)\)")
_TM_PATTERN = re.compile(
    r"(?P<a>-?\d+(?:\.\d+)?)\s+(?P<b>-?\d+(?:\.\d+)?)\s+(?P<c>-?\d+(?:\.\d+)?)\s+"
    r"(?P<d>-?\d+(?:\.\d+)?)\s+(?P<x>-?\d+(?:\.\d+)?)\s+(?P<y>-?\d+(?:\.\d+)?)\s+Tm"
)


def _validate_json_structure(data: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, list):
        return ["JSON root must be a list of categories."]

    for cat_index, category in enumerate(data, start=1):
        if not isinstance(category, dict):
            errors.append(f"Category #{cat_index} must be an object.")
            continue
        name = (category.get("name") or "").strip()
        if not name:
            errors.append(f"Category #{cat_index} missing 'name'.")
        diseases = category.get("diseases")
        if diseases is None:
            errors.append(f"Category '{name or cat_index}' missing 'diseases' list.")
            continue
        if not isinstance(diseases, list):
            errors.append(f"Category '{name or cat_index}' diseases must be a list.")
            continue
        for disease_index, disease in enumerate(diseases, start=1):
            if not isinstance(disease, dict):
                errors.append(f"Disease #{disease_index} in category '{name}' must be an object.")
                continue
            title = (disease.get("name") or "").strip()
            description = (disease.get("description") or "").strip()
            symptoms = (disease.get("symptoms") or "").strip()
            if not any([title, description, symptoms]):
                errors.append(
                    f"Disease #{disease_index} in category '{name}' must have name, description, or symptoms."
                )
    return errors


def _is_csv_header(row: list[str]) -> bool:
    if len(row) < 2:
        return False
    first = row[0].strip().lower()
    second = row[1].strip().lower()
    return ("disease" in first or "symptom" in first) and (
        "cure" in second or "treatment" in second
    )


def load_medical_items(json_path: str, csv_path: str) -> list[MedicalItem]:
    items: list[MedicalItem] = []
    errors: list[str] = []

    json_file = Path(json_path)
    csv_file = Path(csv_path)
    if not json_file.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with json_file.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    errors.extend(_validate_json_structure(data))

    if isinstance(data, list):
        for category in data:
            if not isinstance(category, dict):
                continue
            cat = (category.get("name") or "").strip()
            for disease in category.get("diseases", []):
                if not isinstance(disease, dict):
                    continue
                name = (disease.get("name") or "").strip()
                description = (
                    f"Category: {cat}\n"
                    f"Description: {disease.get('description', '')}\n"
                    f"Transmission: {disease.get('transmission', '')}\n"
                    f"Symptoms: {disease.get('symptoms', '')}\n"
                    f"Treatment: {disease.get('treatment', '')}\n"
                    f"Complications: {disease.get('complications', '')}\n"
                    f"Prevention: {disease.get('prevention', '')}\n"
                ).strip()
                if not name and not description:
                    continue
                items.append(
                    MedicalItem(
                        title=name,
                        description=description,
                        source="json",
                        category=cat,
                    )
                )

    with csv_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header_checked = False
        for row_index, row in enumerate(reader, start=1):
            if not row:
                continue
            if not header_checked:
                header_checked = True
                if _is_csv_header(row):
                    continue
            if len(row) < 2:
                errors.append(f"CSV row #{row_index} must have at least 2 columns.")
                continue
            disease_and_symptoms = row[0].strip()
            cure = row[1].strip()
            if not disease_and_symptoms or not cure:
                errors.append(f"CSV row #{row_index} has empty required fields.")
                continue
            description = f"Disease+Symptoms: {disease_and_symptoms}\nCure: {cure}"
            items.append(
                MedicalItem(
                    title="",
                    description=description.strip(),
                    source="csv",
                )
            )

    if errors:
        raise ValueError("Dataset validation failed:\n- " + "\n- ".join(errors))

    if not items:
        raise ValueError("No valid medical items loaded from dataset files.")

    return items


def discover_pdf_paths(
    dataset_dir: str = "data/dataset",
    *,
    excluded_paths: list[str] | None = None,
) -> list[str]:
    """Discover PDF files in dataset directory, optionally excluding known paths."""
    root = Path(dataset_dir)
    if not root.exists():
        return []

    excluded_names = {Path(path).name for path in (excluded_paths or [])}
    candidates = sorted(path for path in root.glob("*.pdf") if path.is_file())
    return [str(path) for path in candidates if path.name not in excluded_names]


def _decode_pdf_literal(literal: str) -> str:
    """Decode PDF literal strings with basic escape handling."""
    out: list[str] = []
    idx = 0
    while idx < len(literal):
        char = literal[idx]
        if char != "\\":
            out.append(char)
            idx += 1
            continue

        idx += 1
        if idx >= len(literal):
            break
        escaped = literal[idx]
        if escaped in {"\\", "(", ")"}:
            out.append(escaped)
            idx += 1
            continue
        if escaped == "n":
            out.append("\n")
            idx += 1
            continue
        if escaped == "r":
            out.append("\r")
            idx += 1
            continue
        if escaped == "t":
            out.append("\t")
            idx += 1
            continue
        if escaped.isdigit():
            oct_digits = escaped
            idx += 1
            for _ in range(2):
                if idx < len(literal) and literal[idx].isdigit():
                    oct_digits += literal[idx]
                    idx += 1
                else:
                    break
            try:
                out.append(chr(int(oct_digits, 8)))
            except ValueError:
                out.append(oct_digits)
            continue
        out.append(escaped)
        idx += 1
    return "".join(out)


def _extract_text_streams_from_pdf_bytes(pdf_bytes: bytes) -> list[bytes]:
    streams = re.findall(rb"stream\r?\n(.*?)\r?\nendstream", pdf_bytes, flags=re.S)
    text_streams: list[bytes] = []
    for raw_stream in streams:
        payload = raw_stream.lstrip(b"\r\n")
        # Large streams are usually images; skipping them keeps fallback parsing tractable.
        if len(payload) > 500_000:
            continue
        decoded = payload
        try:
            import zlib

            decoded = zlib.decompress(payload)
        except Exception:
            decoded = payload
        if b"Tj" in decoded or b"TJ" in decoded:
            text_streams.append(decoded)
    return text_streams


def _extract_lines_from_text_stream(stream_bytes: bytes) -> list[str]:
    stream_text = stream_bytes.decode("latin1", errors="ignore")
    lines_by_y: list[tuple[float, list[str]]] = []
    current_y = 0.0
    cursor = 0
    while cursor < len(stream_text):
        tm_match = _TM_PATTERN.search(stream_text, cursor)
        tj_match = _PDF_LITERAL_PATTERN.search(stream_text, cursor)
        candidates = [
            ("tm", tm_match.start(), tm_match) if tm_match else None,
            ("tj", tj_match.start(), tj_match) if tj_match else None,
        ]
        candidates = [candidate for candidate in candidates if candidate is not None]
        if not candidates:
            break
        token_type, _, match = min(candidates, key=lambda item: item[1])
        cursor = match.end()
        if token_type == "tm":
            current_y = float(match.group("y"))
            continue

        literal = match.group("literal")
        decoded_literal = _decode_pdf_literal(literal).strip()
        if not decoded_literal:
            continue
        if lines_by_y and abs(lines_by_y[-1][0] - current_y) < 0.7:
            lines_by_y[-1][1].append(decoded_literal)
        else:
            lines_by_y.append((current_y, [decoded_literal]))

    lines: list[str] = []
    for _, parts in lines_by_y:
        normalized = " ".join(part.strip() for part in parts if part.strip())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        if normalized:
            lines.append(normalized)
    if lines:
        return lines

    # Fallback when no Tm coordinates are available but literal text exists.
    fallback_literals = [
        _decode_pdf_literal(match.group("literal")).strip()
        for match in _PDF_LITERAL_PATTERN.finditer(stream_text)
    ]
    fallback_lines = [
        re.sub(r"\s+", " ", value).strip()
        for value in fallback_literals
        if value and value.strip()
    ]
    if fallback_lines:
        return fallback_lines
    return lines


def _fallback_extract_pdf_pages(pdf_path: str) -> list[str]:
    pdf_bytes = Path(pdf_path).read_bytes()
    streams = _extract_text_streams_from_pdf_bytes(pdf_bytes)
    pages: list[str] = []
    for stream_index, stream in enumerate(streams, start=1):
        lines = _extract_lines_from_text_stream(stream)
        if not lines:
            logger.warning("Skipping unreadable fallback page stream #%s from %s", stream_index, pdf_path)
            continue
        pages.append("\n".join(lines))
    return pages


def extract_pdf_pages(pdf_path: str) -> list[str]:
    """Extract page text from PDF using pypdf if available, else fallback parser."""
    source = Path(pdf_path)
    if not source.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(source))
        pages: list[str] = []
        for index, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append(text)
            else:
                logger.warning("Skipping unreadable page %s from %s", index, pdf_path)
        if pages:
            return pages
    except Exception:
        logger.info("pypdf unavailable or failed for %s; using fallback extractor", pdf_path)

    pages = _fallback_extract_pdf_pages(pdf_path)
    if not pages:
        raise ValueError(f"Could not extract readable text from PDF: {pdf_path}")
    return pages


def _looks_like_heading(line: str) -> bool:
    compact = re.sub(r"\s+", " ", line).strip()
    if not compact:
        return False
    if _CHAPTER_PATTERN.match(compact):
        return True
    if _SECTION_PATTERN.match(compact):
        return True
    if compact.isupper() and 2 <= len(compact.split()) <= 14 and len(compact) <= 120:
        return True
    return False


def _is_numbered_item(line: str) -> bool:
    return bool(_NUMBERED_ITEM_PATTERN.match(line.strip()))


def _is_bullet_item(line: str) -> bool:
    return bool(_BULLET_ITEM_PATTERN.match(line.strip()))


def _chunk_id_for(
    source_file: str,
    page: int,
    chapter: str,
    section: str,
    ordinal: int,
    text: str,
) -> str:
    payload = f"{source_file}|{page}|{chapter}|{section}|{ordinal}|{text}".encode("utf-8")
    return hashlib.sha1(payload).hexdigest()[:16]


def _build_chunk(
    source_file: str,
    page: int,
    chapter: str,
    section: str,
    chunk_order: int,
    text: str,
) -> PdfStructuredChunk:
    cleaned_text = re.sub(r"\s+", " ", text).strip()
    return PdfStructuredChunk(
        source_file=source_file,
        page=page,
        chapter=chapter or "unknown",
        section=section or "unknown",
        chunk_id=_chunk_id_for(
            source_file=source_file,
            page=page,
            chapter=chapter or "unknown",
            section=section or "unknown",
            ordinal=chunk_order,
            text=cleaned_text,
        ),
        text=cleaned_text,
        is_list=_is_numbered_item(cleaned_text) or _is_bullet_item(cleaned_text),
    )


def parse_pdf_to_structured_chunks(pdf_path: str) -> list[PdfStructuredChunk]:
    """Parse PDF into metadata-preserving chunks with chapter/section/list hints."""
    pages = extract_pdf_pages(pdf_path)
    source_file = Path(pdf_path).name

    chunks: list[PdfStructuredChunk] = []
    current_chapter = "unknown"
    current_section = "unknown"

    for page_index, page_text in enumerate(pages, start=1):
        raw_lines = [line.strip() for line in page_text.splitlines()]
        lines = [line for line in raw_lines if line]
        if not lines:
            logger.warning("Skipping empty extracted page %s from %s", page_index, source_file)
            continue

        paragraph: list[str] = []
        chunk_order = 1
        line_index = 0
        while line_index < len(lines):
            line = re.sub(r"\s+", " ", lines[line_index]).strip()
            if not line:
                line_index += 1
                continue

            if _looks_like_heading(line):
                if paragraph:
                    chunks.append(
                        _build_chunk(
                            source_file=source_file,
                            page=page_index,
                            chapter=current_chapter,
                            section=current_section,
                            chunk_order=chunk_order,
                            text=" ".join(paragraph),
                        )
                    )
                    chunk_order += 1
                    paragraph = []
                if _CHAPTER_PATTERN.match(line):
                    current_chapter = line
                    current_section = "unknown"
                else:
                    current_section = line
                line_index += 1
                continue

            if _is_numbered_item(line) or _is_bullet_item(line):
                if paragraph:
                    chunks.append(
                        _build_chunk(
                            source_file=source_file,
                            page=page_index,
                            chapter=current_chapter,
                            section=current_section,
                            chunk_order=chunk_order,
                            text=" ".join(paragraph),
                        )
                    )
                    chunk_order += 1
                    paragraph = []
                list_lines = [line]
                line_index += 1
                while line_index < len(lines):
                    next_line = re.sub(r"\s+", " ", lines[line_index]).strip()
                    if not next_line:
                        line_index += 1
                        break
                    if _is_numbered_item(next_line) or _is_bullet_item(next_line):
                        list_lines.append(next_line)
                        line_index += 1
                        continue
                    if _looks_like_heading(next_line):
                        break
                    if len(next_line.split()) <= 3:
                        break
                    list_lines.append(next_line)
                    line_index += 1

                chunks.append(
                    _build_chunk(
                        source_file=source_file,
                        page=page_index,
                        chapter=current_chapter,
                        section=current_section,
                        chunk_order=chunk_order,
                        text="\n".join(list_lines),
                    )
                )
                chunk_order += 1
                continue

            paragraph.append(line)
            if line.endswith(".") and len(" ".join(paragraph)) >= 220:
                chunks.append(
                    _build_chunk(
                        source_file=source_file,
                        page=page_index,
                        chapter=current_chapter,
                        section=current_section,
                        chunk_order=chunk_order,
                        text=" ".join(paragraph),
                    )
                )
                chunk_order += 1
                paragraph = []
            line_index += 1

        if paragraph:
            chunks.append(
                _build_chunk(
                    source_file=source_file,
                    page=page_index,
                    chapter=current_chapter,
                    section=current_section,
                    chunk_order=chunk_order,
                    text=" ".join(paragraph),
                )
            )
    return chunks


def load_pdf_chunks(
    pdf_path: str,
    *,
    chunking_strategy: str = "semantic",
    semantic_chunk_max_chars: int = 700,
    semantic_use_llamaindex: bool = True,
) -> list[PdfStructuredChunk]:
    """Load PDF chunks with selectable rechunking strategy."""
    base_chunks = parse_pdf_to_structured_chunks(pdf_path)
    if not base_chunks:
        return []

    normalized_strategy = (chunking_strategy or "semantic").strip().lower()
    if normalized_strategy == "section":
        return base_chunks

    return chunk_structured_chunks(
        base_chunks,
        strategy=normalized_strategy,
        semantic_max_chars=semantic_chunk_max_chars,
        semantic_use_llamaindex=semantic_use_llamaindex,
    )


def profile_pdf_structure(pdf_path: str, max_chunks_preview: int = 10) -> dict[str, object]:
    try:
        chunks = load_pdf_chunks(pdf_path, chunking_strategy="section")
    except Exception as exc:
        return {
            "source_file": Path(pdf_path).name,
            "chunk_count": 0,
            "pages_detected": 0,
            "chapters_detected": [],
            "sections_detected": [],
            "list_chunk_count": 0,
            "preview": [],
            "parse_error": str(exc),
        }
    if not chunks:
        return {
            "source_file": Path(pdf_path).name,
            "chunk_count": 0,
            "pages_detected": 0,
            "chapters_detected": [],
            "sections_detected": [],
            "list_chunk_count": 0,
            "preview": [],
            "parse_error": None,
        }

    chapters = sorted({chunk.chapter for chunk in chunks if chunk.chapter != "unknown"})
    sections = sorted({chunk.section for chunk in chunks if chunk.section != "unknown"})
    pages_detected = len({chunk.page for chunk in chunks})
    list_chunk_count = sum(1 for chunk in chunks if chunk.is_list)

    preview = [
        {
            "chunk_id": chunk.chunk_id,
            "page": chunk.page,
            "chapter": chunk.chapter,
            "section": chunk.section,
            "is_list": chunk.is_list,
            "text": chunk.text[:220],
        }
        for chunk in chunks[:max_chunks_preview]
    ]
    return {
        "source_file": Path(pdf_path).name,
        "chunk_count": len(chunks),
        "pages_detected": pages_detected,
        "chapters_detected": chapters,
        "sections_detected": sections,
        "list_chunk_count": list_chunk_count,
        "preview": preview,
        "parse_error": None,
    }
