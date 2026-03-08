# P8 TOC Extraction Pipeline Spec (T8.1.1)

Date: 2026-03-07
Task: `T8.1.1`
Source requirement: `docs/raw_idea/json_format.txt`

## Scope

Build a modular pipeline for `data/dataset/DORIN-CURS_SEM2_searchable.pdf` that:
- extracts TOC metadata from page index `1` (the second PDF page)
- maps TOC entries to real content page ranges
- outputs section-level JSON with extracted text

This document defines the module boundaries and typed contracts to implement in `T8.1.2+`.

## Pipeline Stages

1. TOC metadata extraction
- read TOC page with OCR + layout detection
- reconstruct reading order for 2-column layout (left column top->bottom, then right)
- parse chapter/subchapter and start page
- infer end page from the next entry start page
- adjust page mapping with configurable page offset

2. Section content extraction
- extract text for each TOC page range using PyMuPDF first
- when native extraction quality is poor, fallback to PaddleOCR/PP-Structure
- preserve multi-column reading order
- clean repeated headers, footers, and page numbers

3. Export
- emit JSON records with:
`chapter`, `subchapter`, `start_page`, `end_page`, `original_toc_text`, `text`

## Typed Contracts

Defined in `models/contracts.py`:
- `TocExtractionConfig`
- `TocEntry`
- `TocSectionContent`

## Config Surface

Defined in `config/settings.py` and `.env.example`:
- `TOC_PDF_PATH`
- `TOC_PAGE_INDEX`
- `TOC_EXPECTED_COLUMNS`
- `TOC_PAGE_OFFSET`
- `TOC_MIN_NATIVE_TEXT_CHARS`
- `TOC_USE_PP_STRUCTURE_FALLBACK`
- `TOC_OUTPUT_JSON_PATH`

Validation rules:
- TOC page index must be non-negative
- expected column count must be > 0
- minimum native text threshold must be > 0
- output path must be non-empty
- TOC PDF path must exist for ingest-related execution
