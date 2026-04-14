"""Document loading, extraction, and chunk preparation utilities.

This module is the bridge between raw corpus files and retrievable chunks.

Main responsibilities:
- Load tabular datasets (`load_medical_items`).
- Discover and parse corpus files (`discover_*`, `parse_*`).
- Extract PDF text (PyMuPDF-based path) and optional markdown generation helpers.
- Normalize noisy text and preserve document structure hints (headings/lists).
- Build `PdfStructuredChunk` objects and apply rechunking strategies before embeddings.

Typical ingest path:
1) CLI chooses source files.
2) `load_pdf_chunks(...)` detects file type (`.md` vs `.pdf`).
3) Parser returns base structured chunks.
4) Strategy layer may rechunk (`section`, `semantic`).
5) Ingest pipeline embeds and upserts chunks into Qdrant.
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import re
from pathlib import Path
from typing import Iterator

from models import MedicalItem
from models.contracts import PdfStructuredChunk
from rag.chunking.common import clean_line, is_bullet_item, is_markdown_heading, is_numbered_item
from rag.chunking.strategies import chunk_structured_chunks

logger = logging.getLogger(__name__)

_CHAPTER_PATTERN = re.compile(r"^\s*(capitol(?:ul)?\.?\s*\d+|chapter\s+\d+)\b", re.IGNORECASE)
_SECTION_PATTERN = re.compile(r"^\s*\d+(?:\.\d+){1,}\s+\S+")
_SENTENCE_END_PATTERN = re.compile(r"[.!?:;)]$")
_ROMAN_SECTION_PATTERN = re.compile(r"^\s*[IVXLCDM]+\.\s+\S+", re.IGNORECASE)
_MARKDOWN_HEADING_PATTERN = re.compile(r"^\s*(#{1,3})\s+(.+?)\s*$")
_PAGE_MARKDOWN_FILENAME_PATTERN = re.compile(r"^page_(\d+)\.md$")
_RO_MOJIBAKE_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("Å£", "ț"),
    ("Å¢", "Ț"),
    ("ÅŸ", "ș"),
    ("Åž", "Ș"),
    ("ş", "ș"),
    ("Ş", "Ș"),
    ("ţ", "ț"),
    ("Ţ", "Ț"),
    ("Äƒ", "ă"),
    ("Ä‚", "Ă"),
    ("Ã¢", "â"),
    ("Ã‚", "Â"),
    ("Ã®", "î"),
    ("ÃŽ", "Î"),
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
    """Load and validate structured medical items from JSON and CSV datasets."""

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


def discover_markdown_paths(
    dataset_dir: str = "data/dataset",
    *,
    preferred_filename: str = "document.md",
) -> list[str]:
    """Discover markdown files, preferring the configured filename when present."""
    root = Path(dataset_dir)
    if not root.exists():
        return []

    preferred = root / preferred_filename
    if preferred.is_file():
        return [str(preferred)]

    candidates = sorted(path for path in root.glob("*.md") if path.is_file())
    return [str(path) for path in candidates]


def _normalize_extracted_page_text(text: str) -> str:
    """Normalize extracted page text into compact non-empty lines."""

    lines = [clean_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]
    return "\n".join(lines).strip()


def normalize_page_text_for_markdown_llm(text: str) -> str:
    """Normalize extracted page text while preserving heading/list structure for LLM cleanup."""
    if not text or not text.strip():
        return ""

    def _looks_like_markdown_heading(line: str) -> bool:
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
            and len(compact.split()) <= 6
            and "," not in compact
        ):
            words = [word for word in compact.split() if word]
            if words:
                titled = sum(1 for word in words if word[:1].isupper())
                if titled / len(words) >= 0.6:
                    return True
        return False

    def _merge_lines_for_markdown(paragraph_lines: list[str]) -> list[str]:
        merged: list[str] = []
        for raw_line in paragraph_lines:
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

            previous_is_structural = (
                _looks_like_markdown_heading(previous)
                or _is_numbered_item(previous)
                or _is_bullet_item(previous)
            )
            line_is_structural = (
                _looks_like_markdown_heading(line)
                or _is_numbered_item(line)
                or _is_bullet_item(line)
            )
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

    paragraphs: list[list[str]] = []
    current_paragraph: list[str] = []

    for raw_line in text.splitlines():
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            if current_paragraph:
                paragraphs.append(current_paragraph)
                current_paragraph = []
            continue
        current_paragraph.append(line)

    if current_paragraph:
        paragraphs.append(current_paragraph)

    normalized_paragraphs: list[str] = []
    for paragraph_lines in paragraphs:
        merged_lines = _merge_lines_for_markdown(paragraph_lines)
        if merged_lines:
            normalized_paragraphs.append("\n".join(merged_lines).strip())

    return "\n\n".join(block for block in normalized_paragraphs if block).strip()


def _repair_common_mojibake_ro(text: str) -> str:
    def _marker_score(value: str) -> int:
        return sum(value.count(token) for token in ("Ã", "Å", "Ä"))

    candidates: list[str] = [text]

    try:
        candidates.append(text.encode("cp1252", errors="ignore").decode("utf-8", errors="ignore"))
    except Exception:
        pass

    try:
        candidates.append(text.encode("latin1", errors="ignore").decode("utf-8", errors="ignore"))
    except Exception:
        pass

    repaired = min(candidates, key=_marker_score)
    for broken, fixed in _RO_MOJIBAKE_REPLACEMENTS:
        repaired = repaired.replace(broken, fixed)
    return repaired


_MOJIBAKE_HINT_PATTERN = re.compile(r"[ÃÂÄÅÈ]")
_ROMANIAN_DIACRITICS_PATTERN = re.compile(r"[ĂÂÎȘȚăâîșț]")


def _repair_mojibake_line_if_needed(line: str) -> str:
    compact = line.strip()
    if not compact:
        return line
    if not _MOJIBAKE_HINT_PATTERN.search(compact):
        return line

    candidates: list[str] = [line]
    for codec in ("cp1252", "latin1"):
        try:
            candidates.append(line.encode(codec, errors="ignore").decode("utf-8", errors="ignore"))
        except Exception:
            continue

    def _score(value: str) -> tuple[int, int]:
        # Prefer strings with fewer mojibake markers and more Romanian diacritics.
        marker_penalty = sum(value.count(marker) for marker in ("Ã", "Â", "Ä", "Å", "È", "�"))
        diacritics_bonus = len(_ROMANIAN_DIACRITICS_PATTERN.findall(value))
        return (marker_penalty, -diacritics_bonus)

    repaired = min(candidates, key=_score)
    return _repair_common_mojibake_ro(repaired)


def _is_probably_ocr_noise_line(line: str) -> bool:
    compact = re.sub(r"\s+", " ", line).strip()
    if not compact:
        return False
    if _MARKDOWN_HEADING_PATTERN.match(compact):
        return False
    if _is_numbered_item(compact) or _is_bullet_item(compact):
        return False
    if len(compact) < 8:
        return False
    if re.fullmatch(r"[0-9]+(?:[.,][0-9]+)?(?:°C|%)?", compact):
        return False

    symbol_count = len(re.findall(r"[~\\/_{}\[\]<>|`^!$@#%&*=+]", compact))
    alpha_count = len(re.findall(r"[A-Za-zĂÂÎȘȚăâîșț]", compact))
    if alpha_count == 0:
        return True
    if symbol_count >= 4 and symbol_count / max(len(compact), 1) >= 0.12:
        return True
    return False


def _normalize_markdown_for_ingest(text: str) -> str:
    if not text or not text.strip():
        return ""

    cleaned = _strip_markdown_code_fences(text)
    cleaned = _repair_common_mojibake_ro(cleaned)

    normalized_lines: list[str] = []
    for raw_line in cleaned.splitlines():
        line = _repair_mojibake_line_if_needed(raw_line)
        line = line.replace("•", "- ")
        line = line.replace("◦", "- ")
        line = line.replace("▪", "- ")
        line = line.replace("●", "- ")
        line = line.replace("–", "-")
        line = line.replace("—", "-")
        line = re.sub(r"[ \t]+", " ", line).rstrip()

        if _is_probably_ocr_noise_line(line):
            continue

        normalized_lines.append(line)

    normalized = "\n".join(normalized_lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    return normalized


def _split_text_for_llm_cleanup(text: str, *, max_chars: int = 3500) -> list[str]:
    if max_chars <= 0:
        raise ValueError("max_chars must be greater than 0")
    compact = text.strip()
    if not compact:
        return []

    paragraphs = [part.strip() for part in compact.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = paragraph if not current else f"{current}\n\n{paragraph}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current.strip())
            current = ""
        if len(paragraph) <= max_chars:
            current = paragraph
            continue

        # Hard split very large paragraphs to keep request size bounded.
        start = 0
        while start < len(paragraph):
            end = min(start + max_chars, len(paragraph))
            chunks.append(paragraph[start:end].strip())
            start = end
    if current:
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


def _strip_markdown_code_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _postprocess_markdown_cleanup(text: str) -> str:
    """Apply deterministic cleanup for residual encoding/noise artifacts after LLM output."""
    cleaned = _repair_common_mojibake_ro(text)
    cleaned = cleaned.replace("\"7", " ").replace("'7", " ").replace("`7", " ")
    cleaned = cleaned.replace("\\/", " ")

    def _is_noisy_token(token: str) -> bool:
        compact = token.strip()
        if not compact:
            return True
        # Keep bullets, simple punctuation, and numeric values.
        if compact in {"-", "•", "*"}:
            return False
        if re.fullmatch(r"[0-9]+(?:[.,][0-9]+)?(?:Â°C|°C|%)?", compact):
            return False
        if len(compact) < 6:
            return False

        symbol_count = len(re.findall(r"[~\\/_{}\[\]<>|`^!$@#%&*=+]", compact))
        if symbol_count >= 2:
            return True

        alnum_count = len(re.findall(r"[A-Za-zĂÂÎȘȚăâîșț0-9]", compact))
        if alnum_count == 0:
            return True
        non_alnum_ratio = 1.0 - (alnum_count / len(compact))
        return non_alnum_ratio > 0.45

    normalized_lines: list[str] = []
    for raw_line in cleaned.splitlines():
        tokens = raw_line.split()
        kept = [token for token in tokens if not _is_noisy_token(token)]
        normalized = " ".join(kept).strip()
        normalized = re.sub(r"\s+", " ", normalized)
        if normalized:
            normalized_lines.append(normalized)

    merged = "\n".join(normalized_lines)
    merged = re.sub(r"\n{3,}", "\n\n", merged).strip()
    return merged


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


def iter_pdf_pages_with_pymupdf(
    pdf_path: str,
    *,
    start_page: int = 6,
    end_page: int | None = None,
) -> Iterator[tuple[int, str]]:
    """Yield `(human_page_number, normalized_text)` extracted via PyMuPDF."""
    if start_page < 1:
        raise ValueError("start_page must be greater than or equal to 1")
    if end_page is not None and end_page < start_page:
        raise ValueError("end_page must be greater than or equal to start_page")
    source = Path(pdf_path)
    if not source.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        import fitz
    except Exception as exc:
        raise RuntimeError("PyMuPDF (fitz) is required for page-by-page extraction") from exc

    try:
        document = fitz.open(pdf_path)
    except Exception as exc:
        raise ValueError(f"Could not open PDF with PyMuPDF: {pdf_path}") from exc

    try:
        total_pages = int(document.page_count)
        if start_page > total_pages:
            return
        last_page = total_pages if end_page is None else min(end_page, total_pages)
        for human_page in range(start_page, last_page + 1):
            raw_text = document.load_page(human_page - 1).get_text("text") or ""
            normalized = _normalize_extracted_page_text(raw_text)
            if normalized:
                yield human_page, normalized
    finally:
        try:
            document.close()
        except Exception:
            pass


def write_page_markdown(
    *,
    output_dir: str | Path,
    page_number: int,
    markdown_text: str,
) -> Path:
    """Persist one page markdown file as `page_{number}.md`."""
    if page_number < 1:
        raise ValueError("page_number must be greater than or equal to 1")
    if not markdown_text or not markdown_text.strip():
        raise ValueError("markdown_text must be a non-empty string")

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    page_path = root / f"page_{page_number}.md"
    page_path.write_text(markdown_text.strip() + "\n", encoding="utf-8")
    return page_path


def concatenate_page_markdown_files(
    *,
    output_dir: str | Path,
    page_numbers: list[int] | None = None,
    output_filename: str = "document.md",
    separator: str = "\n\n---\n\n",
) -> Path:
    """Concatenate page markdown files into one document in numeric page order."""
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    if page_numbers is None:
        discovered: list[int] = []
        for path in root.glob("page_*.md"):
            match = _PAGE_MARKDOWN_FILENAME_PATTERN.match(path.name)
            if match:
                discovered.append(int(match.group(1)))
        ordered_pages = sorted(set(discovered))
    else:
        ordered_pages = sorted({page for page in page_numbers if page >= 1})

    if not ordered_pages:
        raise ValueError("No page markdown files available for concatenation")

    parts: list[str] = []
    for page_number in ordered_pages:
        page_path = root / f"page_{page_number}.md"
        if not page_path.exists():
            raise FileNotFoundError(f"Missing page markdown file: {page_path}")
        parts.append(page_path.read_text(encoding="utf-8").strip())

    merged_path = root / output_filename
    merged_path.write_text(separator.join(parts).strip() + "\n", encoding="utf-8")
    return merged_path


def extract_pdf_to_markdown(
    *,
    pdf_path: str,
    output_dir: str | Path = "output",
    start_page: int = 6,
    end_page: int | None = None,
    max_pages_per_run: int | None = None,
    provider: str | None = None,
) -> dict[str, object]:
    """Extract and convert PDF pages to markdown files plus merged document."""
    if max_pages_per_run is not None and max_pages_per_run <= 0:
        raise ValueError("max_pages_per_run must be greater than 0 when provided")

    from llm.llm_router import llm_cleanup_pdf_page

    processed_pages: list[int] = []
    failed_pages: list[int] = []
    processed_count = 0

    for page_number, page_text in iter_pdf_pages_with_pymupdf(
        pdf_path,
        start_page=start_page,
        end_page=end_page,
    ):
        if max_pages_per_run is not None and processed_count >= max_pages_per_run:
            break

        normalized = normalize_page_text_for_markdown_llm(page_text)
        if not normalized:
            continue
        normalized = _repair_common_mojibake_ro(normalized)
        cleanup_blocks = _split_text_for_llm_cleanup(normalized, max_chars=3500)
        if not cleanup_blocks:
            continue

        try:
            cleaned_blocks: list[str] = []
            for block in cleanup_blocks:
                response = llm_cleanup_pdf_page(
                    source_file=Path(pdf_path).name,
                    page_number=page_number,
                    page_text=block,
                    provider=provider,
                )
                content = _strip_markdown_code_fences(response.content or "")
                content = _postprocess_markdown_cleanup(content)
                if content:
                    cleaned_blocks.append(content)
            markdown_text = "\n\n".join(cleaned_blocks).strip()
            if not markdown_text:
                markdown_text = normalized
        except Exception:
            failed_pages.append(page_number)
            markdown_text = f"## Extraction Warning\n\n{normalized}"

        write_page_markdown(
            output_dir=output_dir,
            page_number=page_number,
            markdown_text=markdown_text,
        )
        processed_pages.append(page_number)
        processed_count += 1

    if not processed_pages:
        raise ValueError("No pages were processed for markdown extraction")

    merged_path = concatenate_page_markdown_files(
        output_dir=output_dir,
        page_numbers=processed_pages,
    )
    return {
        "source_file": Path(pdf_path).name,
        "output_dir": str(Path(output_dir)),
        "pages_processed": len(processed_pages),
        "page_numbers": processed_pages,
        "failed_pages": failed_pages,
        "document_path": str(merged_path),
    }


def extract_pdf_pages(pdf_path: str) -> list[str]:
    """Extract page text from PDF using PyMuPDF only."""
    source = Path(pdf_path)
    if not source.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    pymupdf_pages = _extract_pages_with_pymupdf(pdf_path)
    if not pymupdf_pages:
        raise ValueError(f"Could not extract readable text with PyMuPDF from PDF: {pdf_path}")

    logger.info("Recovered %s pages with PyMuPDF from %s", len(pymupdf_pages), pdf_path)
    return [pymupdf_pages[index] for index in sorted(pymupdf_pages.keys())]


def _looks_like_heading(line: str) -> bool:
    compact = clean_line(line)
    if not compact:
        return False
    if is_markdown_heading(compact):
        return True
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
    return is_numbered_item(line)


def _is_bullet_item(line: str) -> bool:
    return is_bullet_item(line)


def _is_numbered_heading(line: str, next_line: str | None = None) -> bool:
    compact = clean_line(line)
    if not is_numbered_item(compact):
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
    """Merge wrapped page lines while preserving structural boundaries."""

    merged: list[str] = []
    for raw_line in lines:
        line = clean_line(raw_line)
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
    """Build a stable chunk ID from source metadata and normalized text."""

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
    """Create one normalized structured chunk with deterministic metadata."""

    cleaned_text = clean_line(text)
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


def parse_markdown_to_structured_chunks(markdown_path: str) -> list[PdfStructuredChunk]:
    """Parse markdown into metadata-preserving chunks with heading/list hints."""
    source = Path(markdown_path)
    if not source.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    raw_markdown = source.read_text(encoding="utf-8")
    normalized_markdown = _normalize_markdown_for_ingest(raw_markdown)
    lines = normalized_markdown.splitlines()
    source_file = source.name

    chunks: list[PdfStructuredChunk] = []
    current_chapter = "unknown"
    current_section = "unknown"
    chunk_order = 1
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        nonlocal chunk_order, paragraph
        if not paragraph:
            return
        text = " ".join(paragraph).strip()
        if text:
            chunks.append(
                _build_chunk(
                    source_file=source_file,
                    page=0,
                    chapter=current_chapter,
                    section=current_section,
                    chunk_order=chunk_order,
                    text=text,
                )
            )
            chunk_order += 1
        paragraph = []

    index = 0
    while index < len(lines):
        raw_line = lines[index]
        line = re.sub(r"\s+", " ", raw_line).strip()
        if not line:
            flush_paragraph()
            index += 1
            continue

        heading_match = is_markdown_heading(line) and re.match(r"^\s*(#{1,3})\s+(.+?)\s*$", line)
        if heading_match:
            flush_paragraph()
            level = len(heading_match.group(1))
            heading = heading_match.group(2).strip()
            if level == 1:
                current_chapter = heading or "unknown"
                current_section = "unknown"
            elif level == 2:
                current_section = heading or "unknown"
            else:
                if current_section == "unknown":
                    current_section = heading or "unknown"
                else:
                    current_section = f"{current_section} / {heading}"
            index += 1
            continue

        if _is_numbered_item(line) or _is_bullet_item(line):
            flush_paragraph()
            list_lines = [line]
            index += 1
            while index < len(lines):
                candidate_raw = lines[index]
                candidate = re.sub(r"\s+", " ", candidate_raw).strip()
                if not candidate:
                    index += 1
                    break
                if is_markdown_heading(candidate):
                    break
                if _is_numbered_item(candidate) or _is_bullet_item(candidate):
                    list_lines.append(candidate)
                    index += 1
                    continue
                if candidate_raw.startswith(("  ", "\t")):
                    list_lines.append(candidate)
                    index += 1
                    continue
                break

            chunks.append(
                _build_chunk(
                    source_file=source_file,
                    page=0,
                    chapter=current_chapter,
                    section=current_section,
                    chunk_order=chunk_order,
                    text="\n".join(list_lines),
                )
            )
            chunk_order += 1
            continue

        paragraph.append(line)
        index += 1

    flush_paragraph()
    return chunks


def _semantic_chunk_structured_chunks_with_llamaindex(
    chunks: list[PdfStructuredChunk],
) -> list[PdfStructuredChunk]:
    if not chunks:
        return []

    try:
        from llama_index.core.node_parser import SemanticSplitterNodeParser
        from llama_index.core.schema import Document
    except Exception as exc:
        raise RuntimeError(
            "Semantic chunking requires llama-index-core semantic splitter."
        ) from exc

    parser = SemanticSplitterNodeParser.from_defaults(
        buffer_size=1,
        breakpoint_percentile_threshold=95,
    )

    grouped: dict[tuple[str, int, str, str], list[PdfStructuredChunk]] = {}
    ordered_keys: list[tuple[str, int, str, str]] = []
    for item in chunks:
        key = (item.source_file, item.page, item.chapter, item.section)
        if key not in grouped:
            grouped[key] = []
            ordered_keys.append(key)
        grouped[key].append(item)

    rechunked: list[PdfStructuredChunk] = []
    for key in ordered_keys:
        source_file, page, chapter, section = key
        group = grouped[key]
        merged_text = "\n\n".join(part.text.strip() for part in group if part.text.strip())
        if not merged_text:
            continue
        try:
            nodes = parser.get_nodes_from_documents([Document(text=merged_text)])
        except Exception as exc:
            raise RuntimeError(
                f"LlamaIndex semantic chunking failed for {source_file}:{chapter}:{section}."
            ) from exc

        chunk_order = 1
        for node in nodes:
            text = re.sub(r"\s+", " ", node.get_content()).strip()
            if not text:
                continue
            rechunked.append(
                PdfStructuredChunk(
                    source_file=source_file,
                    page=page,
                    chapter=chapter,
                    section=section,
                    chunk_id=_chunk_id_for(
                        source_file=source_file,
                        page=page,
                        chapter=chapter,
                        section=section,
                        ordinal=chunk_order,
                        text=text,
                    ),
                    text=text,
                    is_list=_is_numbered_item(text) or _is_bullet_item(text),
                )
            )
            chunk_order += 1
    return rechunked


def load_pdf_chunks(
    pdf_path: str,
    *,
    chunking_strategy: str = "semantic",
    semantic_chunk_max_chars: int = 700,
    semantic_use_llamaindex: bool = True,
) -> list[PdfStructuredChunk]:
    """Load markdown or PDF chunks with selectable rechunking strategy."""
    source = Path(pdf_path)
    if source.suffix.lower() == ".md":
        base_chunks = parse_markdown_to_structured_chunks(str(source))
    else:
        base_chunks = parse_pdf_to_structured_chunks(pdf_path)
    if not base_chunks:
        return []

    normalized_strategy = (chunking_strategy or "semantic").strip().lower()
    if normalized_strategy == "section":
        return base_chunks

    if normalized_strategy == "semantic":
        if not semantic_use_llamaindex:
            raise RuntimeError("Semantic chunking requires SEMANTIC_USE_LLAMAINDEX=true.")
        return _semantic_chunk_structured_chunks_with_llamaindex(base_chunks)

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



