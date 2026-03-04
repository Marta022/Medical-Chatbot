# P5 PDF Structure Profile

Date: 2026-03-04
Task scope: `T5.1.1`, `T5.1.2`, `T5.1.3`, `T5.1.4`, `T5.1.TEST`

## Dataset Assignment

- Primary chunking document: `data/dataset/DORIN-CURS_SEM2_searchable.pdf`
- Validation document: `data/dataset/DORIN_GENERALA_CARDIOVASCULARA-RESPIRATORIE-DISESTIVA.CV01.pdf`

## Implemented Extraction Rules

Extraction path:
- Preferred backend: `pypdf` (if installed in runtime)
- Fallback backend: dependency-free stream parser from PDF content streams

Structure detection rules:
- Chapter heading:
  - lines matching `CAPITOLUL <number>` (case-insensitive)
  - lines matching `CHAPTER <number>`
- Section heading:
  - dotted numbering pattern `N.N ...` or deeper (`N.N.N ...`)
  - upper-case short title lines
- List detection:
  - numbered items: `1.`, `2)`, etc.
  - bullet items: `-`, `*`, `•`

Metadata preserved per chunk:
- `source_file`
- `page`
- `chapter`
- `section`
- `chunk_id` (deterministic SHA-1 based short hash)
- `text`
- `is_list`

## Primary PDF Profiling Result

Command used:

```powershell
python - <<'PY'
import logging
from rag.chunking.load_documents import profile_pdf_structure
logging.disable(logging.CRITICAL)
print(profile_pdf_structure("data/dataset/DORIN-CURS_SEM2_searchable.pdf", max_chunks_preview=2))
PY
```

Observed summary:
- `source_file`: `DORIN-CURS_SEM2_searchable.pdf`
- `chunk_count`: `2811`
- `pages_detected`: `618` (fallback streams used as page units when `pypdf` is unavailable)
- `list_chunk_count`: `642`
- `parse_error`: `None`

Notes:
- The primary PDF is readable through the fallback parser.
- Without `pypdf`, page numbering is derived from extracted text stream order, not canonical PDF page tree indices.

## Validation PDF Profiling Result

Command used:

```powershell
python - <<'PY'
import logging
from rag.chunking.load_documents import profile_pdf_structure
logging.disable(logging.CRITICAL)
print(profile_pdf_structure("data/dataset/DORIN_GENERALA_CARDIOVASCULARA-RESPIRATORIE-DISESTIVA.CV01.pdf", max_chunks_preview=2))
PY
```

Observed summary:
- `source_file`: `DORIN_GENERALA_CARDIOVASCULARA-RESPIRATORIE-DISESTIVA.CV01.pdf`
- `chunk_count`: `0`
- `pages_detected`: `0`
- `parse_error`: `Could not extract readable text from PDF: data/dataset/DORIN_GENERALA_CARDIOVASCULARA-RESPIRATORIE-DISESTIVA.CV01.pdf`

Blocker:
- In this environment, external dependency install is blocked, so `pypdf` cannot currently be installed.
- The fallback parser does not recover readable text for this file, likely due encoding/filter differences.

Recommended unblock:
- Install `pypdf` in runtime environment and rerun profiling for validation PDF.
- If still unreadable, add OCR fallback in the upcoming ingestion epic.
