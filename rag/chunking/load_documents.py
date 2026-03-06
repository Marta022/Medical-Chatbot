from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from models import MedicalItem
from models.contracts import PdfStructuredChunk
from rag.chunking.strategies import chunk_structured_chunks

logger = logging.getLogger(__name__)

_CHAPTER_PATTERN = re.compile(r"^\s*(capitol(?:ul)?\.?\s*\d+|chapter\s+\d+)\b", re.IGNORECASE)
_SECTION_PATTERN = re.compile(r"^\s*\d+(?:\.\d+){1,}\s+\S+")
_NUMBERED_ITEM_PATTERN = re.compile(r"^\s*\d+[\.\)]\s+\S+")
_SENTENCE_END_PATTERN = re.compile(r"[.!?:;)]$")
_ROMAN_SECTION_PATTERN = re.compile(r"^\s*[IVXLCDM]+\.\s+\S+", re.IGNORECASE)
_BULLET_ITEM_PATTERN = re.compile(r"^\s*[-*•◦▪▫‣∙◆◇■□✦✧]\s+\S+")
_PDF_LITERAL_PATTERN = re.compile(r"\((?P<literal>(?:\\.|[^\\)])*)\)")
_TM_PATTERN = re.compile(
    r"(?P<a>-?\d+(?:\.\d+)?)\s+(?P<b>-?\d+(?:\.\d+)?)\s+(?P<c>-?\d+(?:\.\d+)?)\s+"
    r"(?P<d>-?\d+(?:\.\d+)?)\s+(?P<x>-?\d+(?:\.\d+)?)\s+(?P<y>-?\d+(?:\.\d+)?)\s+Tm"
)


@dataclass(frozen=True)
class _OcrTextBlock:
    x: float
    y: float
    text: str


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


def _build_lines_from_positioned_fragments(
    fragments: list[tuple[float, float, str]],
) -> list[str]:
    if not fragments:
        return []

    rows: dict[float, list[tuple[float, str]]] = {}
    for x_pos, y_pos, text in fragments:
        clean = re.sub(r"\s+", " ", text).strip()
        if not clean:
            continue
        row_key = round(y_pos * 2) / 2.0
        rows.setdefault(row_key, []).append((x_pos, clean))

    x_values = sorted(x_pos for parts in rows.values() for x_pos, _ in parts)
    split_x: float | None = None
    if len(x_values) >= 12:
        max_gap = 0.0
        max_index = 0
        for index in range(len(x_values) - 1):
            gap = x_values[index + 1] - x_values[index]
            if gap > max_gap:
                max_gap = gap
                max_index = index
        left_count = max_index + 1
        right_count = len(x_values) - left_count
        if (
            max_gap >= 75
            and left_count >= max(4, len(x_values) // 5)
            and right_count >= max(4, len(x_values) // 5)
        ):
            split_x = (x_values[max_index] + x_values[max_index + 1]) / 2.0

    if split_x is None:
        line_records: list[tuple[float, float, str]] = []
        for row_y, parts in rows.items():
            ordered = sorted(parts, key=lambda item: item[0])
            line_text = " ".join(text for _, text in ordered).strip()
            if not line_text:
                continue
            line_records.append((min(x for x, _ in ordered), row_y, line_text))
        line_records = sorted(line_records, key=lambda item: item[1], reverse=True)
        return [record[2] for record in line_records]

    line_records = []
    for row_y, parts in rows.items():
        ordered = sorted(parts, key=lambda item: item[0])
        left_parts = [(x, text) for x, text in ordered if x < split_x]
        right_parts = [(x, text) for x, text in ordered if x >= split_x]
        if left_parts:
            left_text = " ".join(text for _, text in left_parts).strip()
            if left_text:
                line_records.append((min(x for x, _ in left_parts), row_y, left_text))
        if right_parts:
            right_text = " ".join(text for _, text in right_parts).strip()
            if right_text:
                line_records.append((min(x for x, _ in right_parts), row_y, right_text))

    left_col = [record for record in line_records if record[0] < split_x]
    right_col = [record for record in line_records if record[0] >= split_x]
    left_col = sorted(left_col, key=lambda item: item[1], reverse=True)
    right_col = sorted(right_col, key=lambda item: item[1], reverse=True)
    return [record[2] for record in left_col + right_col]


def _extract_page_text_with_columns(page: object) -> str:
    fragments: list[tuple[float, float, str]] = []

    def _visitor(text: str, _cm: object, tm: object, _font_dict: object, _font_size: object) -> None:
        try:
            if not isinstance(tm, (list, tuple)) or len(tm) < 6:
                return
            x_pos = float(tm[4])
            y_pos = float(tm[5])
            if not text or not text.strip():
                return
            fragments.append((x_pos, y_pos, text))
        except Exception:
            return

    try:
        raw_text = page.extract_text(visitor_text=_visitor) or ""
    except TypeError:
        # Older pypdf versions may not expose visitor hooks.
        return (page.extract_text() or "").strip()
    except Exception:
        return (page.extract_text() or "").strip()

    rebuilt_lines = _build_lines_from_positioned_fragments(fragments)
    if rebuilt_lines:
        return "\n".join(rebuilt_lines).strip()
    return raw_text.strip()


def _normalize_extracted_page_text(text: str) -> str:
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def _extract_ocr_blocks_from_image(image: object) -> list[_OcrTextBlock]:
    # Prefer PaddleOCR for higher-quality recognition; keep RapidOCR as a fallback.
    try:
        import numpy as np
        from paddleocr import PaddleOCR
    except Exception:
        np = None  # type: ignore[assignment]
    else:
        try:
            # Romanian language model is used when available.
            ocr_engine = PaddleOCR(use_angle_cls=True, lang="ro", show_log=False)
            result = ocr_engine.ocr(np.array(image), cls=True)
        except Exception:
            result = None

        blocks: list[_OcrTextBlock] = []
        if result:
            for page_result in result:
                if not page_result:
                    continue
                for item in page_result:
                    if not isinstance(item, (list, tuple)) or len(item) < 2:
                        continue
                    points = item[0]
                    rec = item[1]
                    if not isinstance(rec, (list, tuple)) or not rec:
                        continue
                    text = str(rec[0]).strip()
                    if not text:
                        continue
                    try:
                        xs = [float(point[0]) for point in points]
                        ys = [float(point[1]) for point in points]
                        x_pos = min(xs)
                        y_pos = min(ys)
                    except Exception:
                        x_pos = 0.0
                        y_pos = 0.0
                    blocks.append(_OcrTextBlock(x=x_pos, y=y_pos, text=text))
        if blocks:
            return blocks

    try:
        import numpy as np
        from rapidocr_onnxruntime import RapidOCR
    except Exception:
        return []

    try:
        ocr_engine = RapidOCR()
        result, _ = ocr_engine(np.array(image))
    except Exception:
        return []

    if not result:
        return []

    blocks: list[_OcrTextBlock] = []
    for item in result:
        if not isinstance(item, (list, tuple)) or len(item) < 3:
            continue
        points, text, _score = item[0], str(item[1]).strip(), item[2]
        if not text:
            continue
        try:
            xs = [float(point[0]) for point in points]
            ys = [float(point[1]) for point in points]
            x_pos = min(xs)
            y_pos = min(ys)
        except Exception:
            x_pos = 0.0
            y_pos = 0.0
        blocks.append(_OcrTextBlock(x=x_pos, y=y_pos, text=text))
    return blocks


def _rebuild_text_from_ocr_blocks(blocks: list[_OcrTextBlock]) -> str:
    if not blocks:
        return ""

    rows: dict[float, list[_OcrTextBlock]] = {}
    for block in blocks:
        row_key = round(block.y / 12.0) * 12.0
        rows.setdefault(row_key, []).append(block)

    lines: list[str] = []
    for row_key in sorted(rows.keys()):
        row = sorted(rows[row_key], key=lambda item: item.x)
        line = " ".join(item.text.strip() for item in row if item.text.strip())
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)
    return "\n".join(lines).strip()


def _extract_pages_with_rapidocr(
    pdf_path: str,
    *,
    page_indexes: list[int] | None = None,
) -> dict[int, str]:
    try:
        import pypdfium2 as pdfium
    except Exception:
        return {}

    try:
        document = pdfium.PdfDocument(pdf_path)
    except Exception:
        return {}

    try:
        if page_indexes is None:
            targets = list(range(len(document)))
        else:
            targets = sorted({index for index in page_indexes if 0 <= index < len(document)})
        extracted: dict[int, str] = {}
        for index in targets:
            try:
                page = document[index]
                image = page.render(scale=2.0).to_pil()
                blocks = _extract_ocr_blocks_from_image(image)
                text = _rebuild_text_from_ocr_blocks(blocks)
                normalized = _normalize_extracted_page_text(text)
                if normalized:
                    extracted[index] = normalized
            except Exception:
                continue
        return extracted
    finally:
        try:
            document.close()
        except Exception:
            pass


def _extract_pages_with_pymupdf(
    pdf_path: str,
    *,
    page_indexes: list[int] | None = None,
) -> dict[int, str]:
    try:
        import fitz
    except Exception:
        return {}

    try:
        document = fitz.open(pdf_path)
    except Exception:
        return {}

    try:
        if page_indexes is None:
            targets = list(range(document.page_count))
        else:
            targets = sorted(
                {index for index in page_indexes if 0 <= index < document.page_count}
            )

        extracted: dict[int, str] = {}
        for index in targets:
            try:
                text = document.load_page(index).get_text("text")
                normalized = _normalize_extracted_page_text(text or "")
                if normalized:
                    extracted[index] = normalized
            except Exception:
                continue
        return extracted
    finally:
        try:
            document.close()
        except Exception:
            pass


def extract_pdf_pages(pdf_path: str) -> list[str]:
    """Extract page text from PDF using PyMuPDF, then fallback parser/OCR."""
    source = Path(pdf_path)
    if not source.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    pymupdf_pages = _extract_pages_with_pymupdf(pdf_path)
    if pymupdf_pages:
        total_pages = max(pymupdf_pages.keys()) + 1
        missing_indexes = [index for index in range(total_pages) if index not in pymupdf_pages]
        if missing_indexes:
            ocr_pages = _extract_pages_with_rapidocr(pdf_path, page_indexes=missing_indexes)
            if ocr_pages:
                logger.info(
                    "Recovered %s unreadable pages with OCR from %s",
                    len(ocr_pages),
                    pdf_path,
                )
                pymupdf_pages.update(ocr_pages)
        logger.info("Recovered %s pages with PyMuPDF from %s", len(pymupdf_pages), pdf_path)
        return [pymupdf_pages[index] for index in sorted(pymupdf_pages.keys())]

    pages = _fallback_extract_pdf_pages(pdf_path)
    if not pages:
        ocr_pages = _extract_pages_with_rapidocr(pdf_path)
        if ocr_pages:
            logger.info("Recovered %s pages with OCR from %s", len(ocr_pages), pdf_path)
            return [ocr_pages[index] for index in sorted(ocr_pages.keys())]
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
    if _ROMAN_SECTION_PATTERN.match(compact):
        return True
    if compact.isupper() and 2 <= len(compact.split()) <= 14 and len(compact) <= 120:
        return True
    if (
        len(compact) <= 70
        and not _SENTENCE_END_PATTERN.search(compact)
        and compact[:1].isupper()
        and len(compact.split()) <= 5
        and "," not in compact
    ):
        return True
    return False


def _is_numbered_item(line: str) -> bool:
    return bool(_NUMBERED_ITEM_PATTERN.match(line.strip()))


def _is_bullet_item(line: str) -> bool:
    return bool(_BULLET_ITEM_PATTERN.match(line.strip()))


def _is_numbered_heading(line: str, next_line: str | None = None) -> bool:
    compact = re.sub(r"\s+", " ", line).strip()
    if not _NUMBERED_ITEM_PATTERN.match(compact):
        return False
    if _SECTION_PATTERN.match(compact) or _ROMAN_SECTION_PATTERN.match(compact):
        return True

    # Heuristic: short numbered labels are likely subsection titles
    # unless immediately followed by another list marker.
    if len(compact.split()) > 4 or _SENTENCE_END_PATTERN.search(compact):
        return False
    if next_line:
        candidate = re.sub(r"\s+", " ", next_line).strip()
        if _is_numbered_item(candidate) or _is_bullet_item(candidate):
            return False
    return True


def _merge_page_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for raw_line in lines:
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            continue
        if not merged:
            merged.append(line)
            continue

        previous = merged[-1]
        if previous.endswith("-") and line and line[0].islower():
            merged[-1] = f"{previous[:-1]}{line}"
            continue

        previous_is_structural = _looks_like_heading(previous) or _is_numbered_item(previous) or _is_bullet_item(previous)
        line_is_structural = _looks_like_heading(line) or _is_numbered_item(line) or _is_bullet_item(line)
        should_join = (
            not previous_is_structural
            and not line_is_structural
            and not _SENTENCE_END_PATTERN.search(previous)
            and (line[0].islower() or line[0] in {"(", "[", ","})
        )
        if should_join:
            merged[-1] = f"{previous} {line}"
            continue

        merged.append(line)
    return merged


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


def _group_structured_chunks_for_semantic(
    chunks: list[PdfStructuredChunk],
    *,
    group_target_chars: int | None,
) -> list[PdfStructuredChunk]:
    if not chunks:
        return []

    grouped: list[PdfStructuredChunk] = []
    buffer: list[PdfStructuredChunk] = []
    current_key: tuple[str, int, str] | None = None
    current_chars = 0

    def flush_group(items: list[PdfStructuredChunk]) -> None:
        if not items:
            return
        sections = {item.section for item in items if item.section and item.section != "unknown"}
        section = next(iter(sections)) if len(sections) == 1 else "multiple"
        payload = "|".join(item.chunk_id for item in items)
        group_chunk_id = hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]
        text = "\n".join(item.text.strip() for item in items if item.text.strip())
        grouped.append(
            PdfStructuredChunk(
                source_file=items[0].source_file,
                page=items[0].page,
                chapter=items[0].chapter,
                section=section,
                chunk_id=group_chunk_id,
                text=text,
                is_list=any(item.is_list for item in items),
            )
        )

    for item in chunks:
        key = (item.source_file, item.page, item.chapter)
        item_len = len(item.text.strip())
        if not buffer:
            buffer = [item]
            current_key = key
            current_chars = item_len
            continue
        exceeds_group_target = (
            group_target_chars is not None
            and group_target_chars > 0
            and current_chars + item_len > group_target_chars
        )
        if key != current_key or exceeds_group_target:
            flush_group(buffer)
            buffer = [item]
            current_key = key
            current_chars = item_len
            continue
        buffer.append(item)
        current_chars += item_len

    flush_group(buffer)
    return grouped


def parse_pdf_to_structured_chunks(pdf_path: str) -> list[PdfStructuredChunk]:
    """Parse PDF into metadata-preserving chunks with chapter/section/list hints."""
    pages = extract_pdf_pages(pdf_path)
    source_file = Path(pdf_path).name

    chunks: list[PdfStructuredChunk] = []
    current_chapter = "unknown"
    current_section = "unknown"

    for page_index, page_text in enumerate(pages, start=1):
        raw_lines = [line.strip() for line in page_text.splitlines()]
        lines = _merge_page_lines([line for line in raw_lines if line])
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

            next_line: str | None = None
            if line_index + 1 < len(lines):
                next_line = re.sub(r"\s+", " ", lines[line_index + 1]).strip()

            if _looks_like_heading(line) or _is_numbered_heading(line, next_line=next_line):
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

    if normalized_strategy == "semantic":
        grouped_chunks = _group_structured_chunks_for_semantic(
            base_chunks,
            group_target_chars=None,
        )
        return chunk_structured_chunks(
            grouped_chunks,
            strategy=normalized_strategy,
            semantic_max_chars=semantic_chunk_max_chars,
            semantic_use_llamaindex=semantic_use_llamaindex,
        )

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



