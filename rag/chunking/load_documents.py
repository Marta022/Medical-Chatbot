from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from models import MedicalItem
from models.contracts import (
    PdfStructuredChunk,
    TocAgentEntry,
    TocEntry,
    TocPageValidationConfig,
    TocSectionContent,
    TocValidatedEntry,
    TocValidatedSectionContent,
    TocValidationResult,
)
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
_TOC_LINE_PATTERN = re.compile(
    r"^\s*(?P<title>.+?)(?:\s*[.\u2024\u2025\u2026]{2,}\s*|\s+)(?P<page>\d{1,4})\s*$"
)
_PAGE_NUMBER_LINE_PATTERN = re.compile(r"^\s*(?:pagina|page)?\s*\d{1,4}\s*$", re.IGNORECASE)
_PRINTED_PAGE_MARKER_PATTERN = re.compile(
    r"^\s*(?:pag(?:ina)?\.?\s*)?(?P<page>\d{1,4})\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class _OcrTextBlock:
    x: float
    y: float
    text: str


@dataclass(frozen=True)
class _LayoutDetectionResult:
    column_count: int
    split_x: float | None
    method: str


@dataclass(frozen=True)
class _TocLineRecord:
    x: float
    text: str


def _split_block_text_lines(raw_text: str) -> list[str]:
    parts = []
    for line in str(raw_text).splitlines():
        clean = re.sub(r"\s+", " ", line).strip()
        if clean:
            parts.append(clean)
    return parts


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


def _detect_two_column_layout(blocks: list[_OcrTextBlock]) -> _LayoutDetectionResult:
    if len(blocks) < 8:
        return _LayoutDetectionResult(column_count=1, split_x=None, method="insufficient_blocks")

    anchors = sorted(block.x for block in blocks)
    if len(anchors) < 8:
        return _LayoutDetectionResult(column_count=1, split_x=None, method="insufficient_anchors")

    max_gap = 0.0
    max_index = 0
    for index in range(len(anchors) - 1):
        gap = anchors[index + 1] - anchors[index]
        if gap > max_gap:
            max_gap = gap
            max_index = index

    left_count = max_index + 1
    right_count = len(anchors) - left_count
    min_count = max(3, len(anchors) // 5)
    if max_gap >= 40 and left_count >= min_count and right_count >= min_count:
        split_x = (anchors[max_index] + anchors[max_index + 1]) / 2.0
        return _LayoutDetectionResult(column_count=2, split_x=split_x, method="x_gap")
    return _LayoutDetectionResult(column_count=1, split_x=None, method="single_column")


def _build_toc_line_records_from_blocks(
    blocks: list[_OcrTextBlock],
    *,
    expected_columns: int,
) -> list[_TocLineRecord]:
    if not blocks:
        return []

    layout = _detect_two_column_layout(blocks)

    # Group nearby text blocks into visual rows before ordering inside columns.
    rows: dict[float, list[_OcrTextBlock]] = {}
    for block in blocks:
        clean = re.sub(r"\s+", " ", block.text).strip()
        if not clean:
            continue
        row_key = round(block.y / 8.0) * 8.0
        rows.setdefault(row_key, []).append(_OcrTextBlock(x=block.x, y=block.y, text=clean))

    if not rows:
        return []

    if expected_columns == 2 and layout.column_count == 2 and layout.split_x is not None:
        row_records: list[tuple[float, float, str]] = []
        for row_y in sorted(rows.keys()):
            ordered = sorted(rows[row_y], key=lambda item: item.x)
            left_items = [item for item in ordered if item.x < layout.split_x]
            right_items = [item for item in ordered if item.x >= layout.split_x]
            if left_items:
                left_line = " ".join(item.text for item in left_items).strip()
                if left_line:
                    row_records.append(
                        (row_y, min(item.x for item in left_items), left_line)
                    )
            if right_items:
                right_line = " ".join(item.text for item in right_items).strip()
                if right_line:
                    row_records.append(
                        (row_y, min(item.x for item in right_items), right_line)
                    )

        if not row_records:
            return []

        left = [row for row in row_records if row[1] < layout.split_x]
        right = [row for row in row_records if row[1] >= layout.split_x]
        left = sorted(left, key=lambda item: item[0])
        right = sorted(right, key=lambda item: item[0])
        return [_TocLineRecord(x=row[1], text=row[2]) for row in left + right]

    row_records: list[tuple[float, float, str]] = []
    for row_y in sorted(rows.keys()):
        ordered = sorted(rows[row_y], key=lambda item: item.x)
        line = " ".join(item.text for item in ordered).strip()
        if not line:
            continue
        min_x = min(item.x for item in ordered)
        row_records.append((row_y, min_x, line))
    if not row_records:
        return []

    row_records = sorted(row_records, key=lambda item: item[0])
    return [_TocLineRecord(x=row[1], text=row[2]) for row in row_records]


def _build_toc_lines_from_blocks(
    blocks: list[_OcrTextBlock],
    *,
    expected_columns: int,
) -> list[str]:
    records = _build_toc_line_records_from_blocks(
        blocks,
        expected_columns=expected_columns,
    )
    return [record.text for record in records]


def _extract_toc_blocks_with_pymupdf(
    pdf_path: str,
    page_index: int,
) -> list[_OcrTextBlock]:
    try:
        import fitz
    except Exception:
        return []

    try:
        document = fitz.open(pdf_path)
    except Exception:
        return []

    try:
        if page_index < 0 or page_index >= document.page_count:
            return []
        page = document.load_page(page_index)
        raw_blocks = page.get_text("blocks") or []
        blocks: list[_OcrTextBlock] = []
        for block in raw_blocks:
            if not isinstance(block, (list, tuple)) or len(block) < 5:
                continue
            x0, y0, _x1, _y1, text = block[:5]
            lines = _split_block_text_lines(str(text))
            if not lines:
                continue
            try:
                x_pos = float(x0)
                y_pos = float(y0)
            except Exception:
                continue
            for line_index, line in enumerate(lines):
                blocks.append(_OcrTextBlock(x=x_pos, y=y_pos + (line_index * 4.0), text=line))
        return blocks
    finally:
        try:
            document.close()
        except Exception:
            pass


def _extract_toc_blocks_with_ocr(
    pdf_path: str,
    page_index: int,
) -> list[_OcrTextBlock]:
    try:
        import pypdfium2 as pdfium
    except Exception:
        return []

    try:
        document = pdfium.PdfDocument(pdf_path)
    except Exception:
        return []

    try:
        if page_index < 0 or page_index >= len(document):
            return []
        page = document[page_index]
        image = page.render(scale=2.0).to_pil()
        return _extract_ocr_blocks_from_image(image)
    except Exception:
        return []
    finally:
        try:
            document.close()
        except Exception:
            pass


def extract_toc_page_lines(
    pdf_path: str,
    *,
    toc_page_index: int = 1,
    expected_columns: int = 2,
    min_native_text_chars: int = 120,
) -> list[str]:
    source = Path(pdf_path)
    if not source.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    if toc_page_index < 0:
        raise ValueError("toc_page_index must be >= 0")
    if expected_columns <= 0:
        raise ValueError("expected_columns must be > 0")
    if min_native_text_chars <= 0:
        raise ValueError("min_native_text_chars must be > 0")

    native_blocks = _extract_toc_blocks_with_pymupdf(pdf_path, toc_page_index)
    native_chars = sum(len(block.text.strip()) for block in native_blocks)
    if native_blocks and native_chars >= min_native_text_chars:
        lines = _build_toc_lines_from_blocks(native_blocks, expected_columns=expected_columns)
        if lines:
            logger.info(
                "TOC page %s extracted via PyMuPDF blocks with %s lines from %s",
                toc_page_index,
                len(lines),
                pdf_path,
            )
            return lines

    ocr_blocks = _extract_toc_blocks_with_ocr(pdf_path, toc_page_index)
    lines = _build_toc_lines_from_blocks(ocr_blocks, expected_columns=expected_columns)
    if lines:
        logger.info(
            "TOC page %s extracted via OCR blocks with %s lines from %s",
            toc_page_index,
            len(lines),
            pdf_path,
        )
        return lines

    if native_blocks:
        # Last fallback: keep native block ordering if layout-based grouping failed.
        ordered = sorted(native_blocks, key=lambda item: (item.y, item.x))
        fallback_lines = [item.text for item in ordered if item.text.strip()]
        if fallback_lines:
            logger.warning(
                "TOC extraction fallback used native ordering on page %s from %s",
                toc_page_index,
                pdf_path,
            )
            return fallback_lines

    raise ValueError(f"Could not extract readable TOC lines from page {toc_page_index} in {pdf_path}")


def extract_toc_page_records(
    pdf_path: str,
    *,
    toc_page_index: int = 1,
    expected_columns: int = 2,
    min_native_text_chars: int = 120,
) -> list[tuple[float, str]]:
    source = Path(pdf_path)
    if not source.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    if toc_page_index < 0:
        raise ValueError("toc_page_index must be >= 0")
    if expected_columns <= 0:
        raise ValueError("expected_columns must be > 0")
    if min_native_text_chars <= 0:
        raise ValueError("min_native_text_chars must be > 0")

    native_blocks = _extract_toc_blocks_with_pymupdf(pdf_path, toc_page_index)
    native_chars = sum(len(block.text.strip()) for block in native_blocks)
    if native_blocks and native_chars >= min_native_text_chars:
        records = _build_toc_line_records_from_blocks(
            native_blocks,
            expected_columns=expected_columns,
        )
        if records:
            return [(record.x, record.text) for record in records]

    ocr_blocks = _extract_toc_blocks_with_ocr(pdf_path, toc_page_index)
    records = _build_toc_line_records_from_blocks(
        ocr_blocks,
        expected_columns=expected_columns,
    )
    if records:
        return [(record.x, record.text) for record in records]

    if native_blocks:
        ordered = sorted(native_blocks, key=lambda item: (item.y, item.x))
        fallback = [
            (item.x, item.text.strip())
            for item in ordered
            if item.text and item.text.strip()
        ]
        if fallback:
            return fallback
    return []


def _parse_toc_row(line: str) -> tuple[str, int] | None:
    compact = re.sub(r"\s+", " ", line).strip()
    if not compact:
        return None
    match = _TOC_LINE_PATTERN.match(compact)
    if not match:
        return None
    title = re.sub(r"\s+", " ", match.group("title")).strip(" .\t")
    if not title:
        return None
    return title, int(match.group("page"))


def parse_toc_entries(
    toc_records: list[tuple[float, str]],
    *,
    ignored_terms: tuple[str, ...] = ("contents", "cuprins"),
) -> list[TocEntry]:
    if not toc_records:
        return []

    x_values = sorted(x for x, _ in toc_records)
    base_x = x_values[0]
    indent_threshold = 12.0
    distinct = sorted({round(x, 1) for x in x_values})
    if len(distinct) >= 2:
        min_gap = min(
            distinct[index + 1] - distinct[index]
            for index in range(len(distinct) - 1)
        )
        indent_threshold = max(8.0, min(20.0, min_gap * 0.7))

    ignored = {term.strip().lower() for term in ignored_terms if term.strip()}
    entries: list[TocEntry] = []
    current_chapter = ""

    for x_pos, original_line in toc_records:
        parsed = _parse_toc_row(original_line)
        if not parsed:
            continue
        title, start_page = parsed
        if title.strip().lower() in ignored:
            continue

        is_subchapter = (x_pos - base_x) >= indent_threshold
        if is_subchapter:
            chapter = current_chapter or title
            subchapter = title
        else:
            chapter = title
            subchapter = None
            current_chapter = chapter

        entries.append(
            TocEntry(
                chapter=chapter,
                subchapter=subchapter,
                start_page=start_page,
                end_page=start_page,
                original_toc_text=original_line.strip(),
            )
        )

    return entries


def preprocess_toc_records_for_agent(
    toc_records: list[tuple[float, str]],
    *,
    ignored_terms: tuple[str, ...] = ("contents", "cuprins"),
) -> list[tuple[float, str]]:
    """Normalize raw TOC OCR/layout records into deterministic rows for interpretation."""
    if not toc_records:
        return []

    ignored = {term.strip().lower() for term in ignored_terms if term.strip()}
    normalized: list[tuple[float, str]] = []
    current_x: float | None = None
    current_text = ""

    def _flush() -> None:
        nonlocal current_x, current_text
        compact = re.sub(r"\s+", " ", current_text).strip(" .\t")
        if not compact or current_x is None:
            current_x = None
            current_text = ""
            return
        parsed = _parse_toc_row(compact)
        if parsed is not None:
            title, _ = parsed
            if title.strip().lower() not in ignored:
                normalized.append((current_x, compact))
            current_x = None
            current_text = ""
            return
        current_text = compact

    for x_pos, raw_text in toc_records:
        clean = re.sub(r"\s+", " ", str(raw_text)).strip()
        if not clean:
            continue
        if current_x is None:
            current_x = float(x_pos)
            current_text = clean
        else:
            same_indent = abs(float(x_pos) - current_x) <= 12.0
            if same_indent:
                candidate = f"{current_text} {clean}".strip()
                if _parse_toc_row(candidate) is not None:
                    current_text = candidate
                    _flush()
                    continue
            _flush()
            current_x = float(x_pos)
            current_text = clean
        if _parse_toc_row(current_text) is not None:
            _flush()

    _flush()
    return normalized


def _default_agent_toc_interpreter(
    toc_records: list[tuple[float, str]],
    *,
    ignored_terms: tuple[str, ...] = ("contents", "cuprins"),
) -> list[TocAgentEntry]:
    parsed_entries = parse_toc_entries(toc_records, ignored_terms=ignored_terms)
    return [
        TocAgentEntry(
            chapter=entry.chapter,
            subchapter=entry.subchapter,
            printed_start_page=entry.start_page,
            original_toc_text=entry.original_toc_text,
        )
        for entry in parsed_entries
    ]


def interpret_toc_entries_with_agent(
    toc_records: list[tuple[float, str]],
    *,
    ignored_terms: tuple[str, ...] = ("contents", "cuprins"),
    agent_interpreter: Callable[[list[tuple[float, str]]], list[TocAgentEntry]] | None = None,
) -> list[TocAgentEntry]:
    """Build agent-level TOC entries from OCR/layout lines.

    The optional `agent_interpreter` hook lets us inject an LLM-driven parser
    while keeping a deterministic parser fallback.
    """
    normalized_records = preprocess_toc_records_for_agent(
        toc_records,
        ignored_terms=ignored_terms,
    )
    if agent_interpreter is not None:
        interpreted = agent_interpreter(normalized_records)
        return [entry for entry in interpreted if isinstance(entry, TocAgentEntry)]

    return _default_agent_toc_interpreter(normalized_records, ignored_terms=ignored_terms)


def validate_toc_start_pages(
    agent_entries: list[TocAgentEntry],
    *,
    config: TocPageValidationConfig,
    pdf_path: str | None = None,
    expected_columns: int = 2,
    min_native_text_chars: int = 120,
    use_pp_structure_fallback: bool = True,
    page_text_provider: Callable[[int], str] | None = None,
    page_validator: Callable[[TocAgentEntry, TocPageValidationConfig], TocValidatedEntry] | None = None,
) -> TocValidationResult:
    """Resolve printed TOC page numbers to validated PDF start pages.

    A concrete validator can be injected later (header/title anchored lookup).
    Until then, the default behavior maps by expected offset.
    """
    def _default_page_text_provider(page_number: int) -> str:
        if not pdf_path:
            return ""
        native_blocks = _extract_page_blocks_with_pymupdf(pdf_path, page_number - 1)
        native_text = _build_section_page_text(
            native_blocks,
            expected_columns=expected_columns,
        )
        if len(native_text) >= min_native_text_chars:
            return native_text
        if use_pp_structure_fallback:
            fallback_blocks = _extract_page_blocks_with_pp_structure(pdf_path, page_number - 1)
            fallback_text = _build_section_page_text(
                fallback_blocks,
                expected_columns=expected_columns,
            )
            if fallback_text:
                return fallback_text
        return native_text

    provider = page_text_provider or _default_page_text_provider
    max_page = _pdf_page_count(pdf_path) if pdf_path else None

    validated: list[TocValidatedEntry] = []
    for entry in agent_entries:
        if page_validator is not None:
            validated_entry = page_validator(entry, config)
            validated.append(validated_entry)
            continue

        expected_page = max(1, entry.printed_start_page + config.expected_page_offset)
        candidate_pages = range(
            max(1, expected_page - config.search_window),
            expected_page + config.search_window + 1,
        )
        if max_page is not None:
            candidate_pages = [page for page in candidate_pages if page <= max_page]

        best_candidate: tuple[int, int, bool, bool, str | None] | None = None
        title_hint = entry.subchapter or entry.chapter
        normalized_hint = re.sub(r"\s+", " ", title_hint).strip().lower()

        for page_number in candidate_pages:
            page_text = provider(page_number)
            if not page_text.strip():
                continue
            marker = _match_printed_page_marker(page_text, entry.printed_start_page)
            has_marker = marker is not None
            has_title = bool(normalized_hint) and _text_contains_title_hint(page_text, normalized_hint)
            if config.require_title_hint and not has_title:
                continue

            score = 0
            if has_marker:
                score += 3
            if has_title:
                score += 2
            distance = abs(page_number - expected_page)
            if best_candidate is None:
                best_candidate = (score, distance, has_marker, has_title, marker)
                best_page = page_number
                continue
            best_score, best_distance, _, _, _ = best_candidate
            if score > best_score or (score == best_score and distance < best_distance):
                best_candidate = (score, distance, has_marker, has_title, marker)
                best_page = page_number

        if best_candidate is None:
            mapped_page = expected_page
            if max_page is not None:
                mapped_page = min(mapped_page, max_page)
            validated.append(
                TocValidatedEntry(
                    chapter=entry.chapter,
                    subchapter=entry.subchapter,
                    printed_start_page=entry.printed_start_page,
                    validated_start_page=mapped_page,
                    original_toc_text=entry.original_toc_text,
                    page_validation_status="OFFSET_MAPPED",
                    page_validation_method="offset_only",
                )
            )
            continue

        _, _, has_marker, has_title, marker = best_candidate
        if has_marker and has_title:
            status = "MATCHED_HEADER_AND_TITLE"
        elif has_marker:
            status = "MATCHED_HEADER"
        elif has_title:
            status = "MATCHED_TITLE"
        else:
            status = "OFFSET_MAPPED"
        validated.append(
            TocValidatedEntry(
                chapter=entry.chapter,
                subchapter=entry.subchapter,
                printed_start_page=entry.printed_start_page,
                validated_start_page=best_page,
                original_toc_text=entry.original_toc_text,
                page_validation_status=status,
                page_validation_method="window_search",
                matched_page_marker=marker,
                matched_title_hint=title_hint if has_title else None,
            )
        )

    return TocValidationResult(entries=validated, config=config)


def _match_printed_page_marker(page_text: str, printed_start_page: int) -> str | None:
    for line in page_text.splitlines():
        clean = re.sub(r"\s+", " ", line).strip()
        match = _PRINTED_PAGE_MARKER_PATTERN.match(clean)
        if not match:
            continue
        if int(match.group("page")) == printed_start_page:
            return clean
    return None


def _text_contains_title_hint(page_text: str, title_hint: str) -> bool:
    if not title_hint.strip():
        return False
    compact_text = re.sub(r"\s+", " ", page_text).strip().lower()
    compact_hint = re.sub(r"\s+", " ", title_hint).strip().lower()
    if compact_hint in compact_text:
        return True
    hint_tokens = [token for token in re.findall(r"[a-z0-9]+", compact_hint) if len(token) > 2]
    if not hint_tokens:
        return False
    matched_tokens = sum(1 for token in hint_tokens if token in compact_text)
    return matched_tokens >= max(2, len(hint_tokens) // 2)


def resolve_toc_page_ranges(
    toc_entries: list[TocEntry],
    *,
    page_offset: int = 0,
    max_pdf_page: int | None = None,
) -> list[TocEntry]:
    if not toc_entries:
        return []

    resolved: list[TocEntry] = []
    adjusted_starts = [max(1, entry.start_page + page_offset) for entry in toc_entries]
    total_entries = len(toc_entries)

    for index, entry in enumerate(toc_entries):
        start_page = adjusted_starts[index]
        if index + 1 < total_entries:
            next_start = adjusted_starts[index + 1]
            end_page = max(start_page, next_start - 1)
        elif max_pdf_page is not None:
            end_page = max(start_page, max_pdf_page)
        else:
            end_page = start_page

        if max_pdf_page is not None:
            start_page = min(start_page, max_pdf_page)
            end_page = min(end_page, max_pdf_page)
            end_page = max(start_page, end_page)

        resolved.append(
            TocEntry(
                chapter=entry.chapter,
                subchapter=entry.subchapter,
                start_page=start_page,
                end_page=end_page,
                original_toc_text=entry.original_toc_text,
            )
        )

    return resolved


def _extract_page_blocks_with_pymupdf(
    pdf_path: str,
    page_index: int,
) -> list[_OcrTextBlock]:
    try:
        import fitz
    except Exception:
        return []

    try:
        document = fitz.open(pdf_path)
    except Exception:
        return []

    try:
        if page_index < 0 or page_index >= document.page_count:
            return []
        page = document.load_page(page_index)
        raw_blocks = page.get_text("blocks") or []
        blocks: list[_OcrTextBlock] = []
        for block in raw_blocks:
            if not isinstance(block, (list, tuple)) or len(block) < 5:
                continue
            x0, y0, _x1, _y1, text = block[:5]
            lines = _split_block_text_lines(str(text))
            if not lines:
                continue
            try:
                x_pos = float(x0)
                y_pos = float(y0)
            except Exception:
                continue
            for line_index, line in enumerate(lines):
                blocks.append(_OcrTextBlock(x=x_pos, y=y_pos + (line_index * 4.0), text=line))
        return blocks
    finally:
        try:
            document.close()
        except Exception:
            pass


def _extract_page_blocks_with_pp_structure(
    pdf_path: str,
    page_index: int,
) -> list[_OcrTextBlock]:
    try:
        import pypdfium2 as pdfium
    except Exception:
        return []

    try:
        document = pdfium.PdfDocument(pdf_path)
    except Exception:
        return []

    try:
        if page_index < 0 or page_index >= len(document):
            return []
        page = document[page_index]
        image = page.render(scale=2.0).to_pil()

        try:
            import numpy as np
            from paddleocr import PPStructure
        except Exception:
            return _extract_ocr_blocks_from_image(image)

        try:
            engine = PPStructure(show_log=False)
            result = engine(np.array(image))
        except Exception:
            return _extract_ocr_blocks_from_image(image)

        blocks: list[_OcrTextBlock] = []
        for item in result or []:
            if not isinstance(item, dict):
                continue
            bbox = item.get("bbox")
            if not isinstance(bbox, (list, tuple)) or len(bbox) != 4:
                continue
            try:
                x0 = float(bbox[0])
                y0 = float(bbox[1])
            except Exception:
                x0 = 0.0
                y0 = 0.0

            rec_lines = item.get("res")
            if not isinstance(rec_lines, list):
                continue
            for rec in rec_lines:
                if not isinstance(rec, dict):
                    continue
                text = re.sub(r"\s+", " ", str(rec.get("text", ""))).strip()
                if not text:
                    continue
                blocks.append(_OcrTextBlock(x=x0, y=y0, text=text))

        if blocks:
            return blocks
        return _extract_ocr_blocks_from_image(image)
    finally:
        try:
            document.close()
        except Exception:
            pass


def _build_section_page_text(
    blocks: list[_OcrTextBlock],
    *,
    expected_columns: int,
) -> str:
    lines = _build_toc_lines_from_blocks(blocks, expected_columns=expected_columns)
    if not lines:
        return ""
    return _normalize_extracted_page_text("\n".join(lines))


def _clean_section_page_texts(page_texts: list[str]) -> str:
    if not page_texts:
        return ""

    pages_lines: list[list[str]] = []
    for page_text in page_texts:
        lines = [
            re.sub(r"\s+", " ", line).strip()
            for line in page_text.splitlines()
            if re.sub(r"\s+", " ", line).strip()
        ]
        lines = [line for line in lines if not _PAGE_NUMBER_LINE_PATTERN.match(line)]
        pages_lines.append(lines)

    first_counts: dict[str, int] = {}
    last_counts: dict[str, int] = {}
    for lines in pages_lines:
        if not lines:
            continue
        first_counts[lines[0]] = first_counts.get(lines[0], 0) + 1
        if len(lines) > 1:
            last_counts[lines[-1]] = last_counts.get(lines[-1], 0) + 1

    threshold = max(2, len(pages_lines) // 2 + len(pages_lines) % 2)
    repeated_headers = {line for line, count in first_counts.items() if count >= threshold}
    repeated_footers = {line for line, count in last_counts.items() if count >= threshold}

    cleaned_pages: list[str] = []
    for lines in pages_lines:
        if not lines:
            continue
        working = list(lines)
        if working and working[0] in repeated_headers:
            working = working[1:]
        if working and working[-1] in repeated_footers:
            working = working[:-1]
        if working:
            cleaned_pages.append("\n".join(working))

    return _normalize_extracted_page_text("\n".join(cleaned_pages))


def extract_section_text_range(
    pdf_path: str,
    *,
    start_page: int,
    end_page: int,
    expected_columns: int = 2,
    min_native_text_chars: int = 120,
    use_pp_structure_fallback: bool = True,
) -> str:
    source = Path(pdf_path)
    if not source.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    if start_page <= 0:
        raise ValueError("start_page must be > 0")
    if end_page < start_page:
        raise ValueError("end_page must be >= start_page")
    if expected_columns <= 0:
        raise ValueError("expected_columns must be > 0")
    if min_native_text_chars <= 0:
        raise ValueError("min_native_text_chars must be > 0")

    page_texts: list[str] = []
    for page_number in range(start_page, end_page + 1):
        page_index = page_number - 1
        native_blocks = _extract_page_blocks_with_pymupdf(pdf_path, page_index)
        native_text = _build_section_page_text(
            native_blocks,
            expected_columns=expected_columns,
        )
        if len(native_text) >= min_native_text_chars:
            page_texts.append(native_text)
            continue

        if use_pp_structure_fallback:
            fallback_blocks = _extract_page_blocks_with_pp_structure(pdf_path, page_index)
            fallback_text = _build_section_page_text(
                fallback_blocks,
                expected_columns=expected_columns,
            )
            if fallback_text:
                page_texts.append(fallback_text)
                continue

        if native_text:
            page_texts.append(native_text)

    return _clean_section_page_texts(page_texts)


def aggregate_toc_section_contents(
    pdf_path: str,
    toc_entries: list[TocEntry],
    *,
    expected_columns: int = 2,
    min_native_text_chars: int = 120,
    use_pp_structure_fallback: bool = True,
) -> list[TocSectionContent]:
    sections: list[TocSectionContent] = []
    for entry in toc_entries:
        text = extract_section_text_range(
            pdf_path,
            start_page=entry.start_page,
            end_page=entry.end_page,
            expected_columns=expected_columns,
            min_native_text_chars=min_native_text_chars,
            use_pp_structure_fallback=use_pp_structure_fallback,
        )
        if not text.strip():
            continue
        sections.append(
            TocSectionContent(
                chapter=entry.chapter,
                subchapter=entry.subchapter,
                start_page=entry.start_page,
                end_page=entry.end_page,
                original_toc_text=entry.original_toc_text,
                text=text,
            )
        )
    return sections


def aggregate_validated_toc_section_contents(
    pdf_path: str,
    validated_entries: list[TocValidatedEntry],
    *,
    expected_columns: int = 2,
    min_native_text_chars: int = 120,
    use_pp_structure_fallback: bool = True,
) -> list[TocValidatedSectionContent]:
    if not validated_entries:
        return []

    max_page = _pdf_page_count(pdf_path)
    sections: list[TocValidatedSectionContent] = []
    total_entries = len(validated_entries)

    for index, entry in enumerate(validated_entries):
        start_page = entry.validated_start_page
        if index + 1 < total_entries:
            end_page = max(start_page, validated_entries[index + 1].validated_start_page - 1)
        elif max_page is not None:
            end_page = max(start_page, max_page)
        else:
            end_page = start_page

        if max_page is not None:
            start_page = min(start_page, max_page)
            end_page = min(end_page, max_page)
            end_page = max(start_page, end_page)

        text = extract_section_text_range(
            pdf_path,
            start_page=start_page,
            end_page=end_page,
            expected_columns=expected_columns,
            min_native_text_chars=min_native_text_chars,
            use_pp_structure_fallback=use_pp_structure_fallback,
        )
        if not text.strip():
            continue
        sections.append(
            TocValidatedSectionContent(
                chapter=entry.chapter,
                subchapter=entry.subchapter,
                printed_start_page=entry.printed_start_page,
                validated_start_page=start_page,
                validated_end_page=end_page,
                original_toc_text=entry.original_toc_text,
                page_validation_status=entry.page_validation_status,
                page_validation_method=entry.page_validation_method,
                matched_page_marker=entry.matched_page_marker,
                matched_title_hint=entry.matched_title_hint,
                text=text,
            )
        )
    return sections


def _pdf_page_count(pdf_path: str) -> int | None:
    try:
        import fitz
    except Exception:
        fitz = None  # type: ignore[assignment]
    if fitz is not None:
        try:
            document = fitz.open(pdf_path)
            try:
                return int(document.page_count)
            finally:
                document.close()
        except Exception:
            pass

    try:
        import pypdfium2 as pdfium
    except Exception:
        return None

    try:
        document = pdfium.PdfDocument(pdf_path)
        try:
            return int(len(document))
        finally:
            document.close()
    except Exception:
        return None


def export_toc_sections_to_json(
    pdf_path: str,
    *,
    output_json_path: str,
    toc_page_index: int = 1,
    expected_columns: int = 2,
    page_offset: int = 0,
    min_native_text_chars: int = 120,
    use_pp_structure_fallback: bool = True,
    ignored_terms: tuple[str, ...] = ("contents", "cuprins"),
) -> list[TocSectionContent]:
    records = extract_toc_page_records(
        pdf_path,
        toc_page_index=toc_page_index,
        expected_columns=expected_columns,
        min_native_text_chars=min_native_text_chars,
    )
    entries = parse_toc_entries(records, ignored_terms=ignored_terms)
    max_page = _pdf_page_count(pdf_path)
    resolved_entries = resolve_toc_page_ranges(
        entries,
        page_offset=page_offset,
        max_pdf_page=max_page,
    )
    sections = aggregate_toc_section_contents(
        pdf_path,
        resolved_entries,
        expected_columns=expected_columns,
        min_native_text_chars=min_native_text_chars,
        use_pp_structure_fallback=use_pp_structure_fallback,
    )

    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = [section.to_dict() for section in sections]
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return sections


def export_toc_sections_with_validation_to_json(
    pdf_path: str,
    *,
    output_json_path: str,
    toc_entries_json_path: str,
    toc_page_index: int = 1,
    expected_columns: int = 2,
    page_offset: int = 0,
    page_validation_window: int = 2,
    require_title_hint: bool = False,
    min_native_text_chars: int = 120,
    use_pp_structure_fallback: bool = True,
    ignored_terms: tuple[str, ...] = ("contents", "cuprins"),
) -> tuple[list[TocAgentEntry], list[TocValidatedSectionContent]]:
    records = extract_toc_page_records(
        pdf_path,
        toc_page_index=toc_page_index,
        expected_columns=expected_columns,
        min_native_text_chars=min_native_text_chars,
    )
    toc_entries = interpret_toc_entries_with_agent(records, ignored_terms=ignored_terms)

    validation = validate_toc_start_pages(
        toc_entries,
        config=TocPageValidationConfig(
            expected_page_offset=page_offset,
            search_window=page_validation_window,
            require_title_hint=require_title_hint,
        ),
        pdf_path=pdf_path,
        expected_columns=expected_columns,
        min_native_text_chars=min_native_text_chars,
        use_pp_structure_fallback=use_pp_structure_fallback,
    )
    sections = aggregate_validated_toc_section_contents(
        pdf_path,
        validation.entries,
        expected_columns=expected_columns,
        min_native_text_chars=min_native_text_chars,
        use_pp_structure_fallback=use_pp_structure_fallback,
    )

    toc_entries_path = Path(toc_entries_json_path)
    toc_entries_path.parent.mkdir(parents=True, exist_ok=True)
    toc_entries_path.write_text(
        json.dumps([entry.to_dict() for entry in toc_entries], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([section.to_dict() for section in sections], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return toc_entries, sections


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
