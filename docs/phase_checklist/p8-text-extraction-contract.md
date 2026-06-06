# P8 Text Extraction Contract

Date: 2026-03-09
Scope: `T8.1.1` extraction contract and prompt policy for page-level PDF to Markdown conversion
Source requirements: `docs/raw_idea/text_extraction.txt`

## Goal

Define a deterministic contract for converting `data/dataset/DORIN-CURS-searchable.pdf` into markdown pages using PyMuPDF extraction plus per-page LLM cleanup, while preserving source meaning and structure.

## Input Contract

- `pdf_path`: default `data/dataset/DORIN-CURS-searchable.pdf`
- `start_page`: default `6` (human numbering, inclusive)
- `end_page`: optional (human numbering, inclusive)
- `output_dir`: default `output/`
- `llm_provider`: existing provider selection from app settings/router
- `max_pages_per_run`: optional batching guard for long documents

Validation rules:
- fail fast if `pdf_path` does not exist
- fail fast if `start_page < 1`
- if `end_page` is set, require `end_page >= start_page`
- create `output_dir` if missing

## Processing Contract

For each page in range:
1. Read text with PyMuPDF (`fitz`).
2. Run deterministic normalization before LLM:
   - dehyphenate line-break splits (`car-` + next line -> `car`)
   - merge broken lines inside the same paragraph
   - preserve blank-line paragraph boundaries
   - keep numbered/bulleted lines as list candidates
3. Send normalized page text to LLM with strict markdown policy.
4. Save page output to `output/page_{number}.md` where `{number}` is human page number.

After all pages:
5. Concatenate page files in numeric order to `output/document.md`.

## LLM Prompt Policy

System intent:
- convert extracted page text to clean markdown
- preserve original facts and wording as much as possible
- structure headings and lists when clear from source text
- do not add medical claims not present in the page

User payload template:
- page metadata:
  - source file name
  - page number
- normalized page text block
- output requirements:
  - markdown only
  - preserve content fidelity
  - keep list semantics
  - avoid paraphrasing unless needed to repair broken line wraps

Hard constraints for LLM output:
- no preamble/explanations outside markdown content
- no hallucinated sections
- keep uncertain fragments as plain text (do not infer)
- retain clinical units, values, abbreviations, and terminology

## Output Contract

- per-page artifact: `output/page_{number}.md`
- final artifact: `output/document.md`
- concatenation separator: `\n\n---\n\n` between pages
- output encoding: UTF-8

## Error Handling Contract

- if extraction fails for a page:
  - log page failure
  - continue processing next pages
  - append failure summary at end-of-run report
- if LLM call fails for a page:
  - retry with provider retry policy
  - if retries exhausted, persist normalized raw page text as markdown fallback and tag section with `Extraction Warning`

## Performance and Scalability Contract

- pipeline must support `300+` pages without loading full PDF text in memory
- process page-by-page streaming flow
- optional `max_pages_per_run` enables resumable long runs

## Integration Notes

- reuse existing provider/router stack (`llm_hub/*`, `agent/reasoning/providers/*`)
- expose execution through `run.py` command extension
- keep typed IO models in `models/contracts.py` (no ad-hoc runtime dicts)

## Acceptance Mapping (T8.1.1)

- extraction interface and validation rules: defined
- page-level processing sequence: defined
- LLM prompt policy and constraints: defined
- output artifact contract: defined
- large-document handling expectations: defined
