# Backlog Tracker

Last updated: 2026-04-16  
Tracking scope: tasks defined in `docs/backlog.md`

## Tracking Rules

- Update this file after every implementation step (not only at phase end).
- Keep statuses in sync with backlog task IDs.
- Always record actual effort (`Actual h`) when a task is completed.

Status legend:
- `TODO`: not started
- `IN_PROGRESS`: active
- `BLOCKED`: waiting on dependency/decision
- `DONE`: completed and validated

## Global Progress

| Metric | Value |
| --- | --- |
| Planned effort | 446h |
| Completed effort | 446h |
| In-progress effort | 0h |
| Remaining effort | 0h |
| Overall completion | 100% |

## Phase Progress

| Phase | Planned (h) | Done (h) | In Progress (h) | Remaining (h) | Status |
| --- | --- | --- | --- | --- | --- |
| P0 Product Definition and Planning | 28 | 28 | 0 | 0 | DONE |
| P1 Architecture and Codebase Reorganization | 60 | 60 | 0 | 0 | DONE |
| P2 Core Orchestration and Safety Pipeline | 50 | 50 | 0 | 0 | DONE |
| P3 Code Quality and Observability | 40 | 40 | 0 | 0 | DONE |
| P4 Runtime and Delivery | 60 | 60 | 0 | 0 | DONE |
| P5 Semantic Knowledge and Graph-RAG Expansion | 134 | 134 | 0 | 0 | DONE |
| P6 Retrieval Quality Hardening | 26 | 26 | 0 | 0 | DONE |
| P7 Query Recall and Lexical Fallback | 22 | 22 | 0 | 0 | DONE |
| P8 LLM-Assisted PDF Text Extraction to Markdown | 26 | 26 | 0 | 0 | DONE |

## Epic Progress

| Epic ID | Epic | Planned (h) | Done (h) | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| E0.1 | PRD Authoring and Scope Baseline | 16 | 16 | DONE | PRD baseline completed in `docs/prd.md` with requirement traceability |
| E0.2 | Backlog Governance and Tracker Setup | 12 | 12 | DONE | Risk-buffer model and governance dry-run completed |
| E1.1 | Repository Restructuring to Target Layout | 24 | 24 | DONE | Shims finalized, dataset move complete, import/path validation complete |
| E1.2 | Unified CLI Entrypoint | 10 | 10 | DONE | Added `main.py` entrypoint and CLI shims delegate to it (2026-02-15) |
| E1.3 | Configuration and Prompt Normalization | 10 | 10 | DONE | Prompt centralization + startup validation + config tests completed |
| E1.4 | Domain Models and Typed Contracts | 16 | 16 | DONE | Typed flow refactor + serde + guidelines completed |
| E2.1 | Orchestrator and Evaluator Retry Loop | 20 | 20 | DONE | Orchestrator pipeline, evaluator threshold, retry/fallback, and tests completed |
| E2.2 | Guardrail Hardening | 12 | 12 | DONE | Expanded keyword coverage, LLM fallback, safety logging, and tests completed |
| E2.3 | RAG and Ingestion Robustness | 18 | 18 | DONE | Retrieval filters, chunking strategies, validation, dedup, and tests completed |
| E3.1 | Structured Logging | 12 | 12 | DONE | Logging bootstrap module added and wired to CLI entrypoints (2026-02-25) |
| E3.2 | PEP8 Refactor and Static Checks | 14 | 14 | DONE | Lint/format tooling config added (2026-02-25); lint/format gate executed (2026-02-25) |
| E3.3 | Automated Testing and Quality Gates | 14 | 14 | DONE | Coverage gate passed at 82% (2026-02-25) |
| E4.1 | Application Containerization | 10 | 10 | DONE | `docker build --no-cache -t medical-chatbot:test .` and `docker run --rm medical-chatbot:test python main.py --help` succeeded (2026-02-25) |
| E4.2 | Docker Compose Topology | 16 | 16 | DONE | Connectivity/persistence verified; optional profile added; startup/shutdown and compose test evidence captured |
| E4.3 | Operations and Release Documentation | 14 | 14 | DONE | README runbook, PRD/architecture sync, release/acceptance checklist docs, and walk-through validation completed (`T4.3.1`-`T4.3.TEST`) |
| E4.4 | REST API and OpenWebUI Integration | 20 | 20 | DONE | API integration tests completed (see work log step 064) |
| E5.1 | PDF Dataset Baseline and Structure Detection | 16 | 16 | DONE | Validation PDF parsing verified with `pypdf`; parser metadata/tests confirmed |
| E5.2 | Semantic Chunking with LlamaIndex | 22 | 22 | DONE | Semantic adapter, list-preservation, metadata integration, fallback path, and regression tests completed |
| E5.3 | PDF-First Ingestion Pipeline from `/data` | 18 | 18 | DONE | PDF-first discovery, metadata-rich payloads, stable dedup IDs, CLI pdf-only mode, and ingestion tests completed |
| E5.4 | Medical NER Pipeline and Entity Normalization | 20 | 20 | DONE | Rule-based NER extractor, confidence gating, canonical normalization, and chunk-linked entity persistence added with tests |
| E5.5 | Relation Extraction and Kuzu Graph Storage | 26 | 26 | DONE | Relation extraction, graph ingestion/upsert, reconciliation logic, and graph integration tests completed |
| E5.6 | Graph-RAG, Citation Guarantees, and Visualization | 32 | 32 | DONE | Hybrid retrieval, orchestration policy, citation schema, GitNexus integration, API/CLI controls, docs, and integration tests completed |
| E6.1 | Chunk and Retrieval Quality Stabilization | 26 | 26 | DONE | `T6.1.1`-`T6.1.TEST` completed with startup guards, semantic grouping refactor, chunk quality filters, rerank/confidence hardening, diagnostics report, and regression evidence |
| E7.1 | Keyword Fallback and Chunk Debug Tooling | 22 | 22 | DONE | Added column-aware PDF extraction, keyword fallback retrieval, provenance labels, quality keyword probes, baseline artifact, and regression tests |
| E8.1 | PyMuPDF Extraction + LLM Cleanup Pipeline | 26 | 26 | DONE | `T8.1.1`-`T8.1.TEST` completed with extraction contract, PyMuPDF iterator, normalization heuristics, page-level LLM cleanup, output artifacts, CLI controls, and regression tests including large-page-range batching |

## Phase 0 Completion Record

| Task ID | Estimate (h) | Actual (h) | Status | Evidence |
| --- | --- | --- | --- | --- |
| T0.1.1 | 2 | 2 | DONE | Raw idea analysis in work log step 002 |
| T0.1.2 | 4 | 4 | DONE | `docs/prd.md` sections 1-6 |
| T0.1.3 | 2 | 2 | DONE | `docs/prd.md` section 8 |
| T0.1.4 | 2 | 2 | DONE | `docs/prd.md` section 10 |
| T0.1.5 | 3 | 3 | DONE | `docs/prd.md` section 13 |
| T0.1.6 | 1 | 1 | DONE | `docs/prd.md` version/status header |
| T0.1.TEST | 2 | 2 | DONE | `docs/prd.md` section 14 |
| T0.2.1 | 2 | 2 | DONE | `docs/backlog.md` governance rules |
| T0.2.2 | 2 | 2 | DONE | `docs/backlog-tracker.md` metric tables |
| T0.2.3 | 2 | 2 | DONE | `docs/backlog.md` execution rules + DoD |
| T0.2.4 | 2 | 2 | DONE | `docs/backlog.md` estimation/risk-buffer section |
| T0.2.5 | 2 | 2 | DONE | Ongoing work log convention in tracker |
| T0.2.TEST | 2 | 2 | DONE | Tracker lifecycle evidence steps 003-010 |

## Batch Completion Record (T1.1.2 -> T1.4.TEST)

| Task ID | Estimate (h) | Actual (h) | Status | Evidence |
| --- | --- | --- | --- | --- |
| T1.1.2 | 4 | 4 | DONE | New package modules + updated imports and shims |
| T1.1.5 | 3 | 3 | DONE | `knowledge/qdrant/client.py`, `knowledge/qdrant/ingest.py` |
| T1.1.TEST | 2 | 2 | DONE | Import smoke + compileall pass |
| T1.2.1 | 3 | 3 | DONE | `run.py` CLI entrypoint |
| T1.2.2 | 3 | 3 | DONE | CLI modes `chat`, `ingest`, `eval` wired and smoke checked |
| T1.3.1 | 2 | 2 | DONE | Centralized `AppSettings` in `config/settings.py` |
| T1.4.1 | 2 | 2 | DONE | `docs/p1-model-inventory.md` |
| T1.4.2 | 4 | 4 | DONE | `models/contracts.py` + typed integration |
| T1.4.TEST | 2 | 2 | DONE | `tests/test_models.py` passes via `unittest` |

## Phase 1 Completion Record

| Task ID | Estimate (h) | Actual (h) | Status | Evidence |
| --- | --- | --- | --- | --- |
| T1.1.3 | 2 | 2 | DONE | `docs/p1-shim-register.md` + shim TODO markers |
| T1.1.4 | 2 | 2 | DONE | Dataset files moved to `data/dataset/*`, old paths removed |
| T1.1.6 | 3 | 3 | DONE | `docs/p1-import-validation.md` + import/path checks |
| T1.1.7 | 3 | 3 | DONE | `rag/chunking/*` and `rag/retrieval/*` active, legacy wrapper preserved |
| T1.1.8 | 3 | 3 | DONE | `knowledge/qdrant/ingest.py` consumes `rag.chunking.load_documents` |
| T1.2.3 | 2 | 2 | DONE | README updated with CLI run examples |
| T1.2.TEST | 2 | 2 | DONE | `tests/test_cli.py` passes |
| T1.3.2 | 3 | 3 | DONE | Prompt constants centralized in `config/prompts.py` |
| T1.3.3 | 3 | 3 | DONE | Startup validation added in `config/settings.py` |
| T1.3.TEST | 2 | 2 | DONE | `tests/test_config_prompts.py` passes |
| T1.4.3 | 4 | 4 | DONE | Core flows consume typed models (`QueryRequest`, `GuardrailResult`, `RetrievalResult`, `LLMRequest/Response`, `EvaluatorResult`) |
| T1.4.4 | 2 | 2 | DONE | `models/serde.py` added and used by CLI eval output |
| T1.4.5 | 2 | 2 | DONE | `docs/p1-model-guidelines.md` |

## Phase 5 Planned Task Register

| Task ID | Estimate (h) | Actual (h) | Status | Evidence |
| --- | --- | --- | --- | --- |
| T5.1.1 | 4 | 4 | DONE | Structure profiling artifact `docs/p5-pdf-structure-profile.md` created for primary + validation datasets |
| T5.1.2 | 5 | 5 | DONE | Validation profile parse succeeded with `pypdf`: `chunk_count=2534`, `pages_detected=124`, `parse_error=null` |
| T5.1.3 | 3 | 3 | DONE | Added `PdfStructuredChunk` typed contract in `models/contracts.py` |
| T5.1.4 | 2 | 2 | DONE | Added parser diagnostics and unreadable page warnings in PDF extraction flow |
| T5.1.TEST | 2 | 2 | DONE | `python -m unittest tests.test_load_documents tests.test_pdf_structure tests.test_config_prompts tests.test_models -v` OK |
| T5.2.1 | 3 | 3 | DONE | Added dependency + controls: `llama-index-core`, chunking strategy and semantic settings in config/CLI |
| T5.2.2 | 6 | 6 | DONE | Completed semantic chunker adapter integration across strategy + PDF loading + Qdrant ingestion paths |
| T5.2.3 | 4 | 4 | DONE | List-preservation policy verified with numbered/bulleted block regression tests |
| T5.2.4 | 4 | 4 | DONE | Wired PDF metadata payload ingestion in `knowledge/qdrant/ingest.py` using `load_pdf_chunks` |
| T5.2.5 | 3 | 3 | DONE | Fallback path now exercised in ingest + chunking tests when LlamaIndex is unavailable |
| T5.2.TEST | 2 | 2 | DONE | `python -m unittest tests.test_qdrant_ingest tests.test_ingest_helpers tests.test_cli tests.test_pdf_structure tests.test_chunking -v` OK |
| T5.3.1 | 4 | 4 | DONE | Added `discover_pdf_paths` and wired ingest defaults to enumerate `data/dataset/*.pdf` excluding validation PDF |
| T5.3.2 | 4 | 4 | DONE | Qdrant ingest payload hardened with PDF metadata fields (`source_file`, `page`, `chapter`, `section`, `chunk_id`, `is_list`) |
| T5.3.3 | 4 | 4 | DONE | Stable PDF point IDs based on source/page/chunk identity with repeated-run idempotency tests |
| T5.3.4 | 2 | 2 | DONE | Added PDF-first CLI/shim switches via `--pdf-only` and default shim behavior |
| T5.3.TEST | 4 | 4 | DONE | `python -m unittest tests.test_load_documents tests.test_qdrant_ingest tests.test_ingest_helpers tests.test_cli tests.test_pdf_structure tests.test_chunking -v` OK |
| T5.4.1 | 3 | 3 | DONE | Selected deterministic rule-based NER approach and extraction interface in `knowledge/entities/extractor.py` |
| T5.4.2 | 6 | 6 | DONE | Implemented medical entity extraction for disease/symptom/drug/anatomy with typed `MedicalEntity` outputs |
| T5.4.3 | 3 | 3 | DONE | Added configurable confidence threshold (`ENTITY_MIN_CONFIDENCE`) and filtering |
| T5.4.4 | 4 | 4 | DONE | Implemented alias normalization and duplicate merge behavior in entity extraction |
| T5.4.5 | 2 | 2 | DONE | Persisted entity annotations linked to `chunk_id`, `page`, `source_file` in PDF ingest payloads |
| T5.4.TEST | 2 | 2 | DONE | `python -m unittest tests.test_qdrant_ingest tests.test_entities tests.test_config_prompts tests.test_models -v` OK |
| T5.5.1 | 4 | 4 | DONE | Added Kuzu dependency, graph settings, and `knowledge/graph/client.py` abstraction with tests |
| T5.5.2 | 4 | 4 | DONE | Added graph schema statements + installer for required node/edge types and provenance fields with tests |
| T5.5.3 | 6 | 6 | DONE | Implemented predicate extraction (`disease_has_symptom`, `drug_treats_disease`, `condition_causes_symptom`, `disease_differs_from_disease`) in `knowledge/graph/relations.py` |
| T5.5.4 | 6 | 6 | DONE | Implemented graph ingestion/upsert pipeline from PDF chunks + NER output in `knowledge/graph/ingest.py` and wired into `knowledge/qdrant/ingest.py` |
| T5.5.5 | 4 | 4 | DONE | Added reconciliation logic for repeated entities and relations across chunks (`reconcile_entities`, `reconcile_relations`) |
| T5.5.TEST | 2 | 2 | DONE | `python -m unittest tests.test_graph_client tests.test_graph_schema tests.test_graph_relations tests.test_graph_ingest tests.test_qdrant_ingest tests.test_entities tests.test_config_prompts tests.test_models tests.test_cli tests.test_ingest_helpers -v` OK |
| T5.6.1 | 8 | 8 | DONE | Implemented hybrid Graph-RAG retriever merge path in `rag/retrieval/retriever.py` with vector/graph modes |
| T5.6.2 | 5 | 5 | DONE | Added graph traversal depth and merge/rerank policy controls wired through orchestrator + retriever |
| T5.6.3 | 4 | 4 | DONE | Enforced citation output schema (`source_file`, `page`, `section`, `chunk_id`) in hybrid-mode responses |
| T5.6.4 | 8 | 8 | DONE | Implemented GitNexus graph navigation payload builder and API endpoint (`/graph/nexus`) with source-link hooks |
| T5.6.5 | 3 | 3 | DONE | Added API/CLI controls for Graph-RAG retrieval mode and visualization policy hooks |
| T5.6.6 | 2 | 2 | DONE | Updated README runbook for Graph-RAG/GitNexus setup, controls, and troubleshooting |
| T5.6.TEST | 2 | 2 | DONE | `python -m unittest tests.test_graph_client tests.test_graph_schema tests.test_graph_relations tests.test_graph_ingest tests.test_gitnexus tests.test_citations tests.test_retriever tests.test_retrieval_filters tests.test_orchestrator tests.test_config_prompts tests.test_qdrant_ingest tests.test_entities tests.test_models tests.test_cli tests.test_ingest_helpers tests.test_api_engine_endpoints tests.test_api_openai_adapter tests.test_api_config_controls -v` OK |

## Phase 6 Planned Task Register

| Task ID | Estimate (h) | Actual (h) | Status | Evidence |
| --- | --- | --- | --- | --- |
| T6.1.1 | 4 | 4 | DONE | Added startup checks in `config/settings.py` for fallback embeddings and semantic dependency readiness; updated ingest CLI validation path in `run.py`; tests: `python -m unittest tests.test_config_prompts tests.test_cli -v` OK |
| T6.1.2 | 5 | 5 | DONE | Added semantic pre-grouping in `rag/chunking/load_documents.py` (`_group_structured_chunks_for_semantic`) and semantic-load integration; tests: `python -m unittest tests.test_pdf_structure tests.test_chunking -v` OK; quality probe on primary PDF: semantic chunks `7304 -> 1825`, short ratio `<40 chars` `0.259 -> 0.032` |
| T6.1.3 | 4 | 4 | DONE | Added chunk quality gate in `knowledge/qdrant/ingest.py` with list-aware exception path and settings wiring (`config/settings.py`, `run.py`, `.env.example`); tests: `python -m unittest tests.test_qdrant_ingest tests.test_config_prompts tests.test_cli -v` OK |
| T6.1.4 | 5 | 5 | DONE | Added retrieval rerank pass in `rag/retrieval/retriever.py` with query-overlap scoring and configurable candidate window; hardened low-confidence fallback policy in `agent/orchestrator/orchestrator.py`; tests: `python -m unittest tests.test_retriever tests.test_orchestrator tests.test_retrieval_filters tests.test_config_prompts -v` OK |
| T6.1.5 | 4 | 4 | DONE | Added quality diagnostics module `rag/retrieval/quality_report.py` with chunk metrics and retrieval probes; wired ingest CLI flags (`--quality-report`, `--quality-report-path`) in `run.py`; tests: `python -m unittest tests.test_quality_report tests.test_cli tests.test_qdrant_ingest tests.test_config_prompts -v` OK |
| T6.1.TEST | 4 | 4 | DONE | Added benchmark artifact `docs/p6-retrieval-quality-report.md`; regression suite: `python -m unittest tests.test_pdf_structure tests.test_chunking tests.test_qdrant_ingest tests.test_retriever tests.test_retrieval_filters tests.test_orchestrator tests.test_quality_report tests.test_config_prompts tests.test_cli -v` OK (64 tests) |

## Phase 7 Planned Task Register

| Task ID | Estimate (h) | Actual (h) | Status | Evidence |
| --- | --- | --- | --- | --- |
| T7.1.1 | 2 | 2 | DONE | Added baseline artifacts `docs/p7-recall-baseline.md` and `docs/p7-recall-baseline.json` with weak-recall probes including `sindromul cushing` |
| T7.1.2 | 5 | 5 | DONE | Added column-aware extraction + row reflow in `rag/chunking/load_documents.py` (`_extract_page_text_with_columns`, `_build_lines_from_positioned_fragments`) and merged line normalization |
| T7.1.3 | 5 | 5 | DONE | Added keyword fallback retrieval path and trigger policy in `rag/retrieval/retriever.py` (`_keyword_fallback_hits`) with config controls |
| T7.1.4 | 3 | 3 | DONE | Added retrieval provenance in `models/contracts.py` and retriever return paths (`vector`, `keyword_fallback`, `hybrid`, `hybrid+keyword_fallback`) |
| T7.1.5 | 3 | 3 | DONE | Extended quality debug utility (`rag/retrieval/quality_report.py`, `run.py`) with keyword chunk probes and avg word statistics |
| T7.1.TEST | 4 | 4 | DONE | Regression tests added/updated and validated via `python -m unittest -v` (158 tests OK) |

## Phase 8 Planned Task Register

| Task ID | Estimate (h) | Actual (h) | Status | Evidence |
| --- | --- | --- | --- | --- |
| T8.1.1 | 2 | 2 | DONE | Defined extraction, prompt, output, error, and scaling contracts in `docs/p8-text-extraction-contract.md` |
| T8.1.2 | 4 | 4 | DONE | Added `iter_pdf_pages_with_pymupdf` in `rag/chunking/load_documents.py` with default `start_page=6`, configurable range, and validation; tests: `python -m unittest tests.test_pdf_structure -v` |
| T8.1.3 | 4 | 4 | DONE | Added `normalize_page_text_for_markdown_llm` with dehyphenation, paragraph-aware line-join, and heading/list-preserving merge rules; tests: `python -m unittest tests.test_pdf_structure -v` |
| T8.1.4 | 5 | 5 | DONE | Added `llm_cleanup_pdf_page` in `agent/reasoning/llm_router.py`, prompt contract in `config/prompts.py`, and shim export in `llm_hub/router.py`; tests: `python -m unittest tests.test_llm_router tests.test_config_prompts -v` |
| T8.1.5 | 4 | 4 | DONE | Added `write_page_markdown` and `concatenate_page_markdown_files` in `rag/chunking/load_documents.py` for deterministic per-page output and final document merge; tests: `python -m unittest tests.test_pdf_structure -v` |
| T8.1.6 | 3 | 3 | DONE | Added `extract-markdown` CLI command in `run.py` with controls for pdf path/start-end page/output dir/batch/provider, startup validation for extract flow in `config/settings.py`, and orchestration helper `extract_pdf_to_markdown`; tests: `python -m unittest tests.test_cli tests.test_pdf_structure tests.test_config_prompts -v` |
| T8.1.TEST | 4 | 4 | DONE | Added/ran end-to-end extraction regressions including page artifact generation, merged output ordering, CLI control propagation, and simulated `300+` page batching safety; tests: `python -m unittest tests.test_llm_router tests.test_pdf_structure tests.test_cli tests.test_config_prompts -v` |

## Active Task Board

Use this section for current work only (max 10 items at a time).

| Task ID | Task | Estimate (h) | Actual (h) | Owner | Status | Start | End | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T8.1.TEST | Add tests for extraction quality, output artifacts, and large-PDF execution safety | 4 | 4 | Codex | DONE | 2026-03-09 | 2026-03-09 | Added large-page-range batching regression and executed full P8-focused test gate (57 tests OK) |
| T8.1.6 | Add CLI/config controls for input, start page, output path, and batching | 3 | 3 | Codex | DONE | 2026-03-09 | 2026-03-09 | Added `extract-markdown` CLI command and runtime wiring to new extraction pipeline with provider/start-page/output/batch controls |
| T8.1.5 | Implement markdown writer for `output/page_{number}.md` and final concatenation to `output/document.md` | 4 | 4 | Codex | DONE | 2026-03-09 | 2026-03-09 | Added page markdown writer + concatenation helper and tests for file naming/order/empty-directory behavior |
| T8.1.4 | Integrate page-level LLM cleanup/structuring call into existing provider/router infrastructure | 5 | 5 | Codex | DONE | 2026-03-09 | 2026-03-09 | Added router-level page cleanup API and prompt builder; validated with router/config prompt tests |
| T8.1.3 | Implement line-break normalization and heading/list preservation heuristics pre-LLM | 4 | 4 | Codex | DONE | 2026-03-09 | 2026-03-09 | Added pre-LLM normalization helper `normalize_page_text_for_markdown_llm` and regression tests for line-wrap/hyphen/list-heading handling |
| T8.1.2 | Implement PyMuPDF page iterator and text extraction starting at configurable page index (default 6) | 4 | 4 | Codex | DONE | 2026-03-09 | 2026-03-09 | Added `iter_pdf_pages_with_pymupdf` with range validation and default page-6 start; added 3 iterator tests in `tests/test_pdf_structure.py` |
| T8.1.1 | Define extraction contract and prompt policy for page-level markdown conversion | 2 | 2 | Codex | DONE | 2026-03-09 | 2026-03-09 | Added `docs/p8-text-extraction-contract.md` with IO, prompt, output, and error contracts |
| T7.1.TEST | Add regression tests and before/after probe validation for fallback recall | 4 | 4 | Codex | DONE | 2026-03-05 | 2026-03-05 | Added/updated tests for PDF column reflow, keyword fallback retrieval, quality probes, CLI and config; full suite passed |
| T7.1.5 | Extend debug utility with keyword chunk search and chunk-stat output modes | 3 | 3 | Codex | DONE | 2026-03-05 | 2026-03-05 | Added keyword probe args and chunk-level debug probe output in quality report |
| T7.1.4 | Add fallback merge/ranking and retrieval provenance labeling | 3 | 3 | Codex | DONE | 2026-03-05 | 2026-03-05 | Added retrieval provenance contract and orchestrator retrieval logging metadata |
| T7.1.3 | Implement keyword fallback retrieval path with confidence trigger policy | 5 | 5 | Codex | DONE | 2026-03-05 | 2026-03-05 | Added scroll-based lexical candidate scoring fallback with confidence threshold controls |
| T7.1.2 | Improve two-column reconstruction and bullet line-stitch normalization before semantic chunking | 5 | 5 | Codex | DONE | 2026-03-05 | 2026-03-05 | Added column-aware PDF visitor extraction and merged-line dehyphenation/continuation logic |
| T7.1.1 | Build weak-recall probe set and baseline retrieval report from current corpus | 2 | 2 | Codex | DONE | 2026-03-05 | 2026-03-05 | Added P7 baseline report artifacts with weak-recall and keyword evidence |
| T6.1.TEST | Add and run regression tests for chunk quality and retrieval relevance | 4 | 4 | Codex | DONE | 2026-03-05 | 2026-03-05 | Added P6 quality benchmark artifact and ran combined regression suite (64 tests) |
| T6.1.5 | Add ingestion/retrieval quality report (short-chunk ratio, sample hit diagnostics) | 4 | 4 | Codex | DONE | 2026-03-05 | 2026-03-05 | Added quality report builder and ingest CLI emission/output options with tests |
| T6.1.4 | Add retrieval rerank pass and stronger low-confidence filtering policy | 5 | 5 | Codex | DONE | 2026-03-05 | 2026-03-05 | Added rerank logic and stricter fallback confidence policy with retriever/orchestrator regression tests |
| T6.1.3 | Add chunk quality filters (`min chars/words`) with list-aware exceptions | 4 | 4 | Codex | DONE | 2026-03-05 | 2026-03-05 | Added ingest-time quality filtering with configurable thresholds and list-aware exceptions |
| T6.1.2 | Rework semantic rechunking to operate on larger structural groups (not only micro-fragments) | 5 | 5 | Codex | DONE | 2026-03-05 | 2026-03-05 | Added page/chapter semantic pre-grouping and verified reduced fragment rate on primary PDF |
| T6.1.1 | Add startup guard for embedding backend readiness and semantic dependency checks | 4 | 4 | Codex | DONE | 2026-03-05 | 2026-03-05 | Implemented strict startup checks and ingest CLI-aware validation overrides |
| T5.1.1 | Inspect PDF layout and define extraction rules for headings/lists | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | Profiled `DORIN-CURS_SEM2_searchable.pdf` and validation doc in `docs/p5-pdf-structure-profile.md` |
| T5.1.2 | Implement PDF parser with page-aware structural signals | 5 | 5 | Codex | DONE | 2026-03-04 | 2026-03-04 | Validation PDF parse now succeeds with `pypdf` (`pages_detected=124`) |
| T5.2.2 | Implement semantic chunker adapter with structure hints | 6 | 6 | Codex | DONE | 2026-03-04 | 2026-03-04 | Semantic strategy wired end-to-end into PDF load + ingestion paths |
| T5.2.3 | Implement list-preservation policy for numbered/bullet blocks | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | List-aware policy validated by chunking/PDF regression tests |
| T5.2.4 | Attach metadata to chunk models and serialization path | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | PDF chunks now ingested with `source_file/page/chapter/section/chunk_id` payload fields |
| T5.2.5 | Add fallback to existing section/sentence chunkers | 3 | 3 | Codex | DONE | 2026-03-04 | 2026-03-04 | Semantic fallback exercised when LlamaIndex path unavailable |
| T5.2.TEST | Chunking tests for semantic and fallback modes | 2 | 2 | Codex | DONE | 2026-03-04 | 2026-03-04 | `python -m unittest tests.test_qdrant_ingest tests.test_ingest_helpers tests.test_cli tests.test_pdf_structure tests.test_chunking -v` OK |
| T5.3.1 | Extend loaders to enumerate and parse PDFs from `/data/dataset` | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added dataset PDF discovery helper and wired CLI/shim defaults to exclude validation PDF |
| T5.3.2 | Update Qdrant ingest payload schema for structured metadata | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | PDF-first payload now includes page/chapter/section/chunk identifiers |
| T5.3.3 | Update point-id dedup logic to include source/page/chunk identity | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added deterministic PDF point-ID strategy with repeated-run stability test |
| T5.3.4 | Add ingestion CLI/runtime switches for PDF-first mode | 2 | 2 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added `--pdf-only` mode and set shim to PDF-first ingestion |
| T5.3.TEST | PDF ingestion tests with idempotency checks | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | E5.3 ingestion/chunking regression suite passes (26 tests) |
| T5.4.1 | Select NER approach and implement extraction pipeline interface | 3 | 3 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added `knowledge/entities/extractor.py` interface and chunk-level extraction functions |
| T5.4.2 | Implement medical entity extraction and typed outputs | 6 | 6 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added typed `MedicalEntity` contract and disease/symptom/drug/anatomy extraction |
| T5.4.3 | Add confidence scoring and threshold-based filtering | 3 | 3 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added `ENTITY_MIN_CONFIDENCE` setting and extraction-time filtering |
| T5.4.4 | Implement canonical normalization and duplicate merging | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | Alias normalization (`MI`, `HTA`, `BPOC`) and dedup implemented |
| T5.4.5 | Persist entity annotations linked to `chunk_id` and page | 2 | 2 | Codex | DONE | 2026-03-04 | 2026-03-04 | PDF payloads now include `entities` with source/page/chunk metadata |
| T5.4.TEST | NER + normalization tests | 2 | 2 | Codex | DONE | 2026-03-04 | 2026-03-04 | NER/model/config/ingest tests pass (`tests.test_entities`, `tests.test_qdrant_ingest`, `tests.test_models`) |
| T5.5.1 | Add KuzuDB dependency and implement graph client abstraction | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added `kuzu` dependency, graph runtime settings, and `knowledge/graph/client.py` with lazy import + tests |
| T5.5.2 | Design graph schema for entities, relations, and provenance fields | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added `knowledge/graph/schema.py` with schema statements + `ensure_graph_schema` executor and tests |
| T5.5.3 | Implement relation extraction for required medical predicates | 6 | 6 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added `knowledge/graph/relations.py` with required predicate extraction and confidence gating |
| T5.5.4 | Build graph ingestion/upsert pipeline from chunked text and NER output | 6 | 6 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added `knowledge/graph/ingest.py`, schema bootstrap call, and Qdrant ingest integration hooks |
| T5.5.5 | Add reconciliation for repeated entities/relations across chunks | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added entity/relation reconciliation helpers and deterministic graph IDs |
| T5.5.TEST | Graph schema and ingestion tests | 2 | 2 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added graph relation/ingest tests and validated full E5.5 suite (46 tests) |
| T5.6.1 | Implement Graph-RAG retriever that merges vector and graph candidates | 8 | 8 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added hybrid retrieval mode (`vector`/`hybrid`) and graph-candidate merge path in `rag/retrieval/retriever.py` with tests |
| T5.6.2 | Add orchestration policy for graph traversal depth and merge/rerank | 5 | 5 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added hybrid policy controls (`GRAPH_TRAVERSAL_DEPTH`, merge weights) and orchestrator filter injection with rerank tests |
| T5.6.3 | Enforce citation output schema in generated answers | 4 | 4 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added citation formatter/contract and hybrid-mode response citation enforcement in orchestrator |
| T5.6.4 | Integrate GitNexus for graph navigation and source linking | 8 | 8 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added `knowledge/graph/gitnexus.py` payload adapter and API endpoint `GET /graph/nexus` with source-link mapping |
| T5.6.5 | Add API/CLI controls for Graph-RAG and visualization hooks | 3 | 3 | Codex | DONE | 2026-03-04 | 2026-03-04 | Added chat CLI options and API payload controls for retrieval mode + graph policy hook fields |
| T5.6.6 | Update docs/runbooks for graph setup and troubleshooting | 2 | 2 | Codex | DONE | 2026-03-04 | 2026-03-04 | Updated README with Graph-RAG/GitNexus setup controls and troubleshooting runbook |
| T5.6.TEST | Integration tests for Graph-RAG, citations, and visualization APIs | 2 | 2 | Codex | DONE | 2026-03-04 | 2026-03-04 | Validated graph/citation/retrieval/API integration suite (85 tests) |
| T3.1.1 | Create centralized logging configuration | 3 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `config/logging_config.py` and wired setup in CLI entrypoints |
| T3.1.2 | Replace `print` usage in first-party modules | 4 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Replaced runtime `print` usage with logger calls in CLI and chat loop |
| T3.1.3 | Add correlation ID per request/session | 3 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added correlation IDs in CLI and chat loop |
| T3.1.TEST | Tests for logging config and correlation propagation | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | `python -m unittest tests.test_logging -v` OK |
| T3.2.1 | Add lint/format tooling configuration | 3 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `pyproject.toml` with Black and Ruff config |
| T3.2.2 | Refactor first-party modules for PEP8 compliance | 5 | 3 | Codex | DONE | 2026-02-25 | 2026-02-25 | Wrapped long lines and adjusted imports for PEP8 line length |
| T3.2.3 | Add pre-commit hooks for style checks | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `.pre-commit-config.yaml` for Black and Ruff |
| T3.2.4 | Resolve/document dead or empty modules | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `docs/p3-dead-code-registry.md` |
| T3.2.TEST | Execute lint/format gate and record baseline | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | `python -m black .` OK; `python -m ruff check .` OK |
| T3.3.1 | Unit tests for guardrails and evaluator | 4 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `tests/test_evaluator.py` and extended guardrail tests |
| T3.3.2 | Integration tests for orchestration happy/retry paths | 4 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Extended orchestrator tests for retry guidance |
| T3.3.3 | Mocked tests for retrieval and LLM providers | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `tests/test_llm_router.py` and `tests/test_retriever.py` |
| T3.3.4 | Add coverage threshold and CI enforcement | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added coverage config and CI workflow |
| T3.3.TEST | Full suite run and baseline test report | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | `python -m coverage run -m unittest` OK; `python -m coverage report --fail-under=80` OK (82%) |
| T4.1.1 | Add `Dockerfile` with slim runtime and non-root user | 3 | 3 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `Dockerfile` using `python:3.10-slim` and non-root user |
| T4.1.2 | Add `.dockerignore` and optimize dependency layers | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `.dockerignore` for caches, datasets, and local artifacts |
| T4.1.3 | Add healthcheck and startup command | 3 | 3 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added Docker healthcheck and default chat command |
| T4.1.TEST | Build and run container smoke test | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Retry succeeded: image built with `docker build --no-cache -t medical-chatbot:test .`; smoke run `docker run --rm medical-chatbot:test python main.py --help` returned CLI help output |
| T4.2.1 | Create `docker-compose.yml` with app/qdrant/openwebui | 4 | 1.5 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `docker-compose.yml`; validated with `docker compose config` |
| T4.2.2 | Configure volumes, networks, and env wiring | 3 | 1 | Codex | DONE | 2026-02-25 | 2026-02-25 | Named volumes and bridge network wired; app env maps Qdrant service URL; validated with `docker compose config` |
| T4.2.3 | Ensure app resolves qdrant and persistence works | 3 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | `docker exec medical-chatbot-app ... http://qdrant:6333/collections` returned `200`; persistence probe survived qdrant restart |
| T4.2.4 | Add optional profiles for provider integrations | 2 | 1 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `ollama` service with `local-llm` profile in compose; validated using `docker compose --profile local-llm config --services` |
| T4.2.5 | Validate compose startup/shutdown scenarios | 2 | 1 | Codex | DONE | 2026-02-25 | 2026-02-25 | Verified `up`, `stop/start`, and `down` lifecycle for `app` and `qdrant` |
| T4.2.TEST | Compose integration tests and logs validation | 2 | 1 | Codex | DONE | 2026-02-25 | 2026-02-25 | `docker compose ps` healthy/running states validated; qdrant logs show collection recovery on restart |
| T4.3.1 | Update README with CLI, ingestion, Docker flows | 4 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added Docker/Compose usage section to `README.md` |
| T4.3.2 | Align `docs/prd.md` and architecture diagram with implementation | 3 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Updated `docs/prd.md` version/status and implementation snapshot; updated `architecture.mmd` to current CLI/orchestrator flow and planned API integration |
| T4.3.3 | Add release/demo checklist and risk register | 3 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `docs/release-demo-checklist.md` with release checks, demo flow, and formal risk register; linked in `README.md` docs index |
| T4.3.4 | Add final acceptance checklist mapped to PRD | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `docs/final-acceptance-checklist.md` with FR/NFR mapping, status, and evidence; linked in `README.md` docs index |
| T4.3.TEST | Perform docs walk-through validation | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Validated `python main.py --help`, `python main.py eval`, and documented compose lifecycle (`docker compose up -d qdrant app`, `docker compose ps`, `docker compose down`) |
| T4.4.1 | Create API application skeleton and dependency wiring | 4 | 3 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added Flask app scaffold in `api/app.py`, dependency container in `api/dependencies.py`, package exports in `api/__init__.py`, and scaffold tests in `tests/test_api_scaffold.py` |
| T4.4.2 | Implement engine endpoints (`/health`, `/chat`, `/ingest`, `/eval`) | 5 | 4 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `/chat`, `/ingest`, `/eval` routes in `api/app.py` with typed request handling and consistent JSON errors; validated with `tests/test_api_engine_endpoints.py` |
| T4.4.3 | Implement OpenAI-compatible adapter (`/v1/models`, `/v1/chat/completions`) | 5 | 4 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added adapter endpoints in `api/app.py`; mapped chat-completions payloads to orchestrator and returned OpenAI-compatible response shape; validated with `tests/test_api_openai_adapter.py` |
| T4.4.4 | Add API config for auth, limits, and environment controls | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added `config/api_config.py` and wired auth/limit/env enforcement in `api/app.py`; updated `.env.example`; validated with `tests/test_api_config_controls.py` |
| T4.4.5 | Update compose/docs for OpenWebUI -> API integration | 2 | 2 | Codex | DONE | 2026-02-25 | 2026-02-25 | Added dedicated `api` service and OpenWebUI adapter env wiring in `docker-compose.yml`; updated README integration runbook and API URLs; validated with `docker compose config` |

## Work Log

| Step | Date | Action | Output | Next |
| --- | --- | --- | --- | --- |
| 001 | 2026-02-13 | Reviewed repository structure and first-party modules | Identified missing evaluator implementation, missing Docker assets, dual entrypoints, and logger gap | Build detailed backlog with estimates |
| 002 | 2026-02-13 | Reviewed `docs/raw_idea/licenta_title.txt` and `docs/raw_idea/raw_backlog.txt` | Extracted explicit requirements: PRD conversion, PEP8 refactor, CLI startup, Docker stack, structural reorg | Map requirements to phases/epics/stories/tasks |
| 003 | 2026-02-13 | Created `docs/backlog.md` with phase/epic/story/task breakdown and subtotals | Baseline backlog created (174h total planned) | Start execution from P0/E0.1 |
| 004 | 2026-02-13 | Created `docs/backlog-tracker.md` | Baseline tracker initialized | Update this file on every implementation step |
| 005 | 2026-02-13 | Enhanced `docs/backlog.md` with technical descriptions, deliverables, dependencies, and acceptance criteria per epic | Backlog upgraded for independent developer handover | Start implementation from first `TODO` in P0 |
| 006 | 2026-02-13 | Added mandatory per-epic testing, typed-modeling epic, and REST/OpenWebUI integration epic to backlog | Planned effort updated to 238h and tracker synchronized | Start execution from P0 then prioritize E1.4 before P2 |
| 007 | 2026-02-13 | Normalized active task board to configured maximum item count | Active board kept at 10 items for focus | Keep rotating board items as tasks complete |
| 008 | 2026-02-13 | Reviewed backlog vs tracker and marked already-completed planning activities | Tracker now reflects 12h completed across P0 tasks | Continue with `T0.1.2` and `T0.2.4` |
| 009 | 2026-02-13 | Added formal estimation and risk-buffer policy to backlog governance | Completed `T0.2.4` deliverable | Finalize Phase 0 by completing PRD tasks |
| 010 | 2026-02-13 | Created `docs/prd.md` with goals, requirements, NFR metrics, ownership mapping, traceability matrix, rollout, risks, and validation checklist | Completed remaining E0.1 tasks and closed Phase 0 | Start Phase 1 implementation (`T1.1.1`) |
| 011 | 2026-02-13 | Added Phase 0 completion record with per-task evidence and actual effort | Phase 0 closeout is auditable without reopening old notes | Begin P1 execution board tracking |
| 012 | 2026-02-13 | Created phase-1 migration planning artifact with target tree, old->new mapping, wave plan, shim strategy, and validation checklist | Completed `T1.1.1` and started E1.1 execution | Continue with `T1.1.2` file moves |
| 013 | 2026-02-13 | Executed migration implementation: created new packages (`agent`, `knowledge`, `rag/retrieval`, `rag/chunking`, `models`), added compatibility shims, added centralized settings defaults, and introduced CLI with subcommands | Completed tasks `T1.1.2`, `T1.1.5`, `T1.2.1`, `T1.2.2`, `T1.3.1`, `T1.4.1`, `T1.4.2` | Run validation tasks (`T1.1.TEST`, `T1.4.TEST`) |
| 014 | 2026-02-13 | Ran structure/model validations: import smoke, compileall, CLI help/eval smoke, and model mapping tests | Completed `T1.1.TEST` and `T1.4.TEST` | Rotate active board to next pending P1 tasks |
| 015 | 2026-02-13 | Completed remaining Phase 1 implementation work: shim register, dataset path finalization, startup validation, prompt centralization, typed flow/serde integration, README runbook updates, and model ownership docs | Completed tasks `T1.1.3`, `T1.1.4`, `T1.1.6`, `T1.1.7`, `T1.1.8`, `T1.2.3`, `T1.3.2`, `T1.3.3`, `T1.4.3`, `T1.4.4`, `T1.4.5` | Execute Phase 1 test suite and close phase |
| 016 | 2026-02-13 | Ran full Phase 1 validation suite: CLI smoke, eval smoke, compileall, legacy shim import smoke, and unittest modules (`test_models`, `test_cli`, `test_config_prompts`, `test_phase1_structure`) | Completed `T1.2.TEST` and `T1.3.TEST`; Phase 1 closed | Start Phase 2 tasks (`T2.1.1`) |
| 017 | 2026-02-13 | Re-ran Phase 1 completion validation in active session (`run.py --help`, `run.py eval`, Phase-1 unittest suite, compileall) and re-checked tracker consistency | Confirmed all Phase 1 tasks remain `DONE` with passing validation evidence | Proceed with Phase 2 execution from active board |
| 018 | 2026-02-15 | Added canonical `main.py` CLI entrypoint, updated legacy shims (`app.py`, `agents/main_agent.py`) to delegate to CLI, and refreshed README examples | E1.2 entrypoint alignment tightened without changing behavior | Resume Phase 2 work (`T2.1.1`) |
| 019 | 2026-02-15 | Re-ran Phase-1 validations: compileall + unittest suite (excluding CLI due to timeout) | `python -m compileall agent knowledge rag models config run.py app.py main.py` OK; `python -m unittest tests.test_models tests.test_config_prompts tests.test_phase1_structure -v` OK; `python -m unittest tests.test_cli -v` timed out after 30s | Investigate CLI test hang before next Phase 1 evidence refresh |
| 020 | 2026-02-15 | Implemented orchestrator pipeline with evaluator integration, retry guidance, and provider fallback; added `OrchestratorResponse` model; updated chat loop to use orchestrator; added orchestrator unit tests | Phase-2 epic E2.1 in progress; tests pending (`tests/test_orchestrator.py`) | Run `python -m unittest tests.test_orchestrator -v` |
| 021 | 2026-02-15 | Ran orchestrator tests and closed E2.1 epic | `python -m unittest tests.test_orchestrator -v` OK | Proceed to E2.2 (`T2.2.1`) |
| 022 | 2026-02-15 | Wired orchestrator translation helpers through dependency injection and re-ran tests | `python -m unittest tests.test_orchestrator -v` OK | Continue E2.2 |
| 023 | 2026-02-15 | Hardened guardrails: expanded emergency/unsafe phrases, added LLM fallback handling, safety logging, and guardrail tests | `python -m unittest tests.test_guardrail -v` OK | Proceed to E2.3 (`T2.3.1`) |
| 024 | 2026-02-15 | Implemented RAG/ingestion robustness: retrieval filters, low-confidence fallback, chunking strategies, dataset validation, and idempotent ingestion; added unit tests | `python -m unittest tests.test_orchestrator tests.test_chunking tests.test_retrieval_filters tests.test_ingest_helpers -v` OK | Start E3.1 (`T3.1.1`) |
| 025 | 2026-02-25 | Added centralized logging bootstrap module and wired CLI entrypoints to initialize logging | `config/logging_config.py`, updates to `run.py` and `ingestion/ingest_vectordb.py` | Proceed to T3.1.2 (`print` replacement) |
| 026 | 2026-02-25 | Replaced runtime `print` usage with logger calls in CLI and chat loop | `run.py`, `agent/orchestrator/chat_loop.py`, `ingestion/ingest_vectordb.py` | Proceed to T3.1.3 (correlation IDs) |
| 027 | 2026-02-25 | Added correlation IDs for CLI/ingest and per chat request | `run.py`, `agent/orchestrator/chat_loop.py`, `ingestion/ingest_vectordb.py` | Proceed to T3.1.TEST (logging tests) |
| 028 | 2026-02-25 | Added logging configuration tests for handler/filter and correlation IDs | `tests/test_logging.py` | Run `python -m unittest tests.test_logging -v` |
| 029 | 2026-02-25 | Ran logging tests | `python -m unittest tests.test_logging -v` OK | Proceed to E3.2 (`T3.2.1`) |
| 030 | 2026-02-25 | Added lint/format tooling configuration | `pyproject.toml` (Black, Ruff) | Proceed to T3.2.2 (PEP8 refactor) |
| 031 | 2026-02-25 | Refactored long lines to meet PEP8 line length | `run.py`, `config/settings.py`, `rag/chunking/load_documents.py`, `tests/test_config_prompts.py`, `tests/test_logging.py`, `tests/test_models.py` | Proceed to T3.2.3 (pre-commit hooks) |
| 032 | 2026-02-25 | Added pre-commit hooks for Black and Ruff | `.pre-commit-config.yaml` | Proceed to T3.2.4 (dead/empty modules) |
| 033 | 2026-02-25 | Added dead code registry for empty modules and shims | `docs/p3-dead-code-registry.md` | Proceed to T3.2.TEST (lint/format gate) |
| 034 | 2026-02-25 | Attempted to install lint/format tools for T3.2.TEST | `python -m pip install black ruff` failed (no network access) | Await tool availability or offline install |
| 035 | 2026-02-25 | Ran lint/format gate after installing tools | `python -m black .` OK; `python -m ruff check .` OK | Proceed to E3.3 (`T3.3.1`) |
| 036 | 2026-02-25 | Added evaluator unit tests and extended guardrail tests | `python -m unittest tests.test_guardrail -v` OK; `python -m unittest tests.test_evaluator -v` OK | Proceed to T3.3.2 (orchestrator integration tests) |
| 037 | 2026-02-25 | Added orchestrator retry guidance test and ran orchestrator suite | `python -m unittest tests.test_orchestrator -v` OK | Proceed to T3.3.3 (mocked retrieval/LLM tests) |
| 038 | 2026-02-25 | Added mocked LLM router and retriever tests | `python -m unittest tests.test_llm_router tests.test_retriever -v` OK | Proceed to T3.3.4 (coverage/CI gate) |
| 039 | 2026-02-25 | Added coverage config and CI workflow | `pyproject.toml`, `requirements.txt`, `.github/workflows/ci.yml` | Proceed to T3.3.TEST (full suite + coverage) |
| 040 | 2026-02-25 | Ran full suite with coverage | `python -m coverage run -m unittest` OK; `python -m coverage report --fail-under=80` FAILED (69%) | Add tests or adjust threshold to unblock |
| 041 | 2026-02-25 | Added test coverage for shims/providers/translator/embeddings/loaders and reran coverage | `python -m coverage run -m unittest` OK; `python -m coverage report --fail-under=80` OK (82%) | Proceed to P4 (runtime and delivery) |
| 042 | 2026-02-25 | Added Dockerfile for containerized runtime | `Dockerfile` | Proceed to T4.1.2 (`.dockerignore`) |
| 043 | 2026-02-25 | Added `.dockerignore` for build context hygiene | `.dockerignore` | Proceed to T4.1.3 (healthcheck/startup) |
| 044 | 2026-02-25 | Added Docker healthcheck and default startup command | `Dockerfile` | Proceed to T4.1.TEST (container smoke) |
| 045 | 2026-02-25 | Attempted T4.1 container smoke test commands | `docker --version` OK; `docker compose version` OK; `docker build -t medical-chatbot:test .` FAILED (`Access is denied` lock file in sandbox) and retry outside sandbox FAILED (daemon pipe missing); `docker info` confirms server unavailable | Start Docker Desktop engine, then rerun T4.1.TEST |
| 046 | 2026-02-25 | Re-ran T4.1 smoke after Docker Desktop start | `docker info` OK (server reachable); `docker build -t medical-chatbot:test .` repeatedly fails on layer extraction (`sha256:41f10...` / `unpigz ... corrupted -- invalid deflate data`); `docker builder prune -af` executed; retry still unstable; image listed but `docker run --rm medical-chatbot:test ...` fails with same extraction error | Restart Docker Desktop and clean Docker data/cache before rerunning T4.1.TEST |
| 047 | 2026-02-25 | Implemented compose topology baseline for E4.2 | Added `docker-compose.yml` with `app`, `qdrant`, `openwebui`, named volumes, and shared bridge network; added `.env.example`; `docker compose config` validation passed | Proceed to T4.2.2 connectivity and persistence checks |
| 048 | 2026-02-25 | Finalized compose wiring task | Confirmed volumes/networks/env wiring through compose validation output | Proceed to T4.2.3 service connectivity and persistence behavior check |
| 049 | 2026-02-25 | Synced tracker/backlog execution status and activated next task | Marked `E3.2` as `DONE`, rolled up P4 progress with completed E4.2 baseline tasks, set `T4.2.3` to `IN_PROGRESS`, and kept `T4.1.TEST` as `BLOCKED` pending Docker repair | Repair Docker Desktop image layer cache, then execute `T4.2.3` and unblock `T4.1.TEST` |
| 050 | 2026-02-25 | Completed compose connectivity and persistence verification | `docker exec` from app to `http://qdrant:6333/collections` returned `200`; temporary collection remained `green` after qdrant restart | Proceed to T4.2.4 optional profiles |
| 051 | 2026-02-25 | Added optional provider profile wiring to compose | Added `ollama` service under `local-llm` profile; validated with `docker compose --profile local-llm config --services` | Proceed to T4.2.5 startup/shutdown validation |
| 052 | 2026-02-25 | Executed compose startup/shutdown and integration-log checks | Verified `up`, `stop/start`, `down`, and logs/ps evidence for app+qdrant lifecycle; completed `T4.2.5` and `T4.2.TEST`; closed `E4.2` | Proceed to E4.3 (`T4.3.1`) |
| 053 | 2026-02-25 | Updated operations runbook in README | Added Docker build/compose flows, profile usage, and service URLs to `README.md`; completed `T4.3.1` | Continue E4.3 with `T4.3.2` PRD/architecture alignment |
| 054 | 2026-02-25 | Retried blocked container smoke task (`T4.1.TEST`) | Docker daemon reachable; `docker build --no-cache -t medical-chatbot:test .` completed and `docker run --rm medical-chatbot:test python main.py --help` succeeded | Clear E4.1 blocker and continue E4.3 (`T4.3.2`) |
| 055 | 2026-02-25 | Aligned PRD and architecture diagram to the implemented system | Updated `docs/prd.md` to version `1.1` with implementation snapshot and ownership alignment; updated `architecture.mmd` to CLI -> orchestrator -> guardrail/retrieval/LLM/evaluator flow plus planned API path | Proceed to `T4.3.3` release/demo checklist and risk register |
| 056 | 2026-02-25 | Added release/demo checklist and risk register artifact | Created `docs/release-demo-checklist.md` with release readiness checks, demo run flow, and risk register; linked artifact in `README.md` | Proceed to `T4.3.4` final acceptance checklist mapped to PRD |
| 057 | 2026-02-25 | Added PRD-mapped final acceptance checklist | Created `docs/final-acceptance-checklist.md` with FR/NFR acceptance status and evidence references; linked in `README.md` docs index | Proceed to `T4.3.TEST` docs walk-through validation |
| 058 | 2026-02-25 | Executed docs walk-through validation for E4.3 | `python main.py --help` and `python main.py eval` succeeded; compose walkthrough (`up/ps/down`) succeeded for `qdrant` + `app` | Close E4.3 and proceed to E4.4 (`T4.4.1`) |
| 059 | 2026-02-25 | Implemented API scaffold and dependency wiring | Added `create_app` Flask scaffold with dependency container and standardized error payloads; added `/health` skeleton route and API scaffold tests (`python -m unittest tests.test_api_scaffold -v` OK) | Proceed to `T4.4.2` engine endpoints (`/chat`, `/ingest`, `/eval`) |
| 060 | 2026-02-25 | Implemented engine API endpoints and endpoint tests | Added `/chat`, `/ingest`, and `/eval` endpoint handlers with typed payload validation and JSON error schema; validated with `python -m unittest tests.test_api_scaffold tests.test_api_engine_endpoints -v` | Proceed to `T4.4.3` OpenAI-compatible adapter endpoints |
| 061 | 2026-02-25 | Implemented OpenAI-compatible adapter endpoints and tests | Added `/v1/models` and `/v1/chat/completions` routes with OpenAI-compatible payload/response structure and request validation; validated with `python -m unittest tests.test_api_scaffold tests.test_api_engine_endpoints tests.test_api_openai_adapter -v` | Proceed to `T4.4.4` API config for auth/limits/env controls |
| 062 | 2026-02-25 | Implemented API config controls for auth/limits/env | Added `ApiSettings` config loader (`config/api_config.py`), enforced API enabled/auth/api-key/request limits in `api/app.py`, and added `.env.example` controls; validated with `python -m unittest tests.test_api_scaffold tests.test_api_engine_endpoints tests.test_api_openai_adapter tests.test_api_config_controls -v` | Proceed to `T4.4.5` compose/docs OpenWebUI -> API integration updates |
| 063 | 2026-02-25 | Completed OpenWebUI -> API integration wiring and docs | Updated `docker-compose.yml` with separate `api` service (`python -m api.app`), mapped OpenWebUI to `http://api:8000/v1`, and documented integration in README; compose model validation passed | Proceed to `T4.4.TEST` API integration and compatibility validation |
| 064 | 2026-03-01 | Ran API integration tests for `T4.4.TEST` | Full suite timed out; individual runs OK: `python -m unittest tests.test_api_scaffold -v`, `tests.test_api_engine_endpoints -v`, `tests.test_api_openai_adapter -v`, `tests.test_api_config_controls -v` | Re-run full API suite |
| 065 | 2026-03-01 | Re-ran full API test suite with faulthandler | `python -X faulthandler -m unittest tests.test_api_scaffold tests.test_api_engine_endpoints tests.test_api_openai_adapter tests.test_api_config_controls -v -f` OK (15 tests) | Run overall unittest suite |
| 066 | 2026-03-01 | Ran overall test suite | `python -m unittest -v` OK (84 tests, ~19s) | Backlog closed |
| 067 | 2026-03-04 | Extended backlog/tracker with new PDF-semantic-graph requirements | Added Phase P5 (`E5.1`-`E5.6`, 134h) in `docs/backlog.md`; synchronized tracker totals/status and activated `T5.1.1` | Implement `T5.1.1` parser discovery on `data/dataset/*.pdf` |
| 068 | 2026-03-04 | Implemented first-pass PDF structure parser and typed chunk metadata | Added parser utilities and structured chunk pipeline in `rag/chunking/load_documents.py`; added `PdfStructuredChunk` in `models/contracts.py`; added tests in `tests/test_pdf_structure.py` | Run E5.1 parser test gate and generate profile artifact |
| 069 | 2026-03-04 | Completed E5.1 discovery/testing artifacts and recorded validation blocker | Added `docs/p5-pdf-structure-profile.md`; ran `python -m unittest tests.test_load_documents tests.test_pdf_structure tests.test_config_prompts tests.test_models -v` (OK); validation PDF parsing blocked without `pypdf` availability | Unblock dependency installation, then complete `T5.1.2` on validation dataset |
| 070 | 2026-03-04 | Cleared E5.1 validation blocker after `pypdf` install | Ran validation parse profile on `DORIN_GENERALA...` with `parse_error=null`, `pages_detected=124`, `chunk_count=2534`; marked `T5.1.2` and `E5.1` as DONE | Start E5.2 semantic chunking implementation |
| 071 | 2026-03-04 | Started E5.2 implementation (semantic chunking baseline) | Added semantic chunking adapter/fallback + list-preserving policy in `rag/chunking/strategies.py`; added config+CLI controls (`config/settings.py`, `run.py`, `ingestion/ingest_vectordb.py`); added tests (`tests/test_chunking.py`, `tests/test_config_prompts.py`, `tests/test_cli.py`) | Continue T5.2.2-T5.2.TEST and wire semantic chunking into PDF ingestion flow |
| 072 | 2026-03-04 | Wired semantic chunking into PDF load path and expanded test gate | Added `load_pdf_chunks` in `rag/chunking/load_documents.py` to parse+rechunk with metadata retention; updated exports; added PDF semantic loading tests; ran `python -m unittest tests.test_pdf_structure tests.test_chunking tests.test_config_prompts tests.test_cli -v` (OK) | Continue T5.2.4/T5.2.TEST toward full epic completion |
| 073 | 2026-03-04 | Wired PDF chunk metadata ingestion into Qdrant and closed E5.2 subtask test gates | Extended `knowledge/qdrant/ingest.py` to ingest `load_pdf_chunks` output with metadata-rich payloads; added deterministic PDF point IDs and ingest tests; ran `python -m unittest tests.test_qdrant_ingest tests.test_ingest_helpers tests.test_cli tests.test_pdf_structure tests.test_chunking -v` (OK) | Finish remaining T5.2.2 semantic adapter polish and close E5.2 |
| 074 | 2026-03-04 | Closed E5.2 semantic chunking epic | Finalized semantic adapter integration across strategy/PDF load/Qdrant ingest paths and revalidated API compatibility (`python -m unittest tests.test_api_engine_endpoints tests.test_api_openai_adapter tests.test_api_config_controls -v` OK) | Start E5.3 (`T5.3.1`) |
| 075 | 2026-03-04 | Started E5.3 PDF discovery integration with validation-doc exclusion policy | Added `discover_pdf_paths` in `rag/chunking/load_documents.py`; wired `run.py ingest` and `ingestion/ingest_vectordb.py` to enumerate `data/dataset/*.pdf` while excluding `DORIN_GENERALA...`; added loader test and ran `python -m unittest tests.test_load_documents tests.test_qdrant_ingest tests.test_ingest_helpers tests.test_cli -v` (OK) | Continue T5.3.1 and begin T5.3.2 payload schema hardening |
| 076 | 2026-03-04 | Completed E5.3 PDF-first ingestion pipeline | Added PDF-only ingest mode (`--pdf-only`), finalized metadata-rich PDF payloads and stable point IDs in `knowledge/qdrant/ingest.py`, updated defaults to learn from `DORIN-CURS...` while excluding validation doc, and validated with `python -m unittest tests.test_load_documents tests.test_qdrant_ingest tests.test_ingest_helpers tests.test_cli tests.test_pdf_structure tests.test_chunking -v` plus API compatibility suite | Start E5.4 (`T5.4.1`) |
| 077 | 2026-03-04 | Completed E5.4 NER baseline with normalization and persistence | Added typed entity model (`MedicalEntity`), rule-based extractor + disease lexicon loading in `knowledge/entities/extractor.py`, confidence threshold config (`ENTITY_MIN_CONFIDENCE`), and entity persistence in PDF ingest payloads; validated with `python -m unittest tests.test_qdrant_ingest tests.test_entities tests.test_config_prompts tests.test_models -v` | Start E5.5 (`T5.5.1`) |
| 078 | 2026-03-04 | Completed E5.5 task T5.5.1 and activated T5.5.2 | Added Kuzu dependency (`requirements.txt`), graph backend settings (`GRAPH_BACKEND`, `KUZU_DB_PATH`) in `config/settings.py`, and graph client abstraction in `knowledge/graph/client.py`; validated with `python -m unittest tests.test_graph_client tests.test_config_prompts tests.test_qdrant_ingest tests.test_entities tests.test_models -v` (OK) | Implement `T5.5.2` graph schema definition and tests |
| 079 | 2026-03-04 | Completed E5.5 task T5.5.2 and activated T5.5.3 | Added graph schema module (`knowledge/graph/schema.py`) with node/edge definitions for required predicates and provenance fields (`source_file`, `page`, `chunk_id`, `confidence`) plus schema tests; validated with `python -m unittest tests.test_graph_client tests.test_graph_schema tests.test_config_prompts tests.test_qdrant_ingest tests.test_entities tests.test_models -v` (OK) | Implement `T5.5.3` relation extraction module and tests |
| 080 | 2026-03-04 | Completed E5.5 relation extraction, graph ingest/upsert, reconciliation, and test gate | Added `knowledge/graph/relations.py` (required predicates), `knowledge/graph/ingest.py` (schema bootstrap + upsert pipeline + dedup helpers), `knowledge/graph/ids.py`, wired graph ingest controls into settings/CLI/Qdrant ingest, and added graph tests (`tests.test_graph_relations`, `tests.test_graph_ingest`); validated with `python -m unittest tests.test_graph_client tests.test_graph_schema tests.test_graph_relations tests.test_graph_ingest tests.test_qdrant_ingest tests.test_entities tests.test_config_prompts tests.test_models tests.test_cli tests.test_ingest_helpers -v` (OK) | Start E5.6 (`T5.6.1`) |
| 081 | 2026-03-04 | Completed E5.6 task T5.6.1 and activated T5.6.2 | Added hybrid retrieval baseline in `rag/retrieval/retriever.py` with vector/graph mode dispatch, graph-seeded candidate expansion, and merged ranking; added retrieval mode settings (`RETRIEVAL_MODE`, `GRAPH_RETRIEVAL_TOP_K`) and tests (`tests.test_retriever`, `tests.test_config_prompts`); validated with `python -m unittest tests.test_graph_client tests.test_graph_schema tests.test_graph_relations tests.test_graph_ingest tests.test_retriever tests.test_retrieval_filters tests.test_orchestrator tests.test_config_prompts tests.test_qdrant_ingest tests.test_entities tests.test_models tests.test_cli tests.test_ingest_helpers -v` (OK) | Implement `T5.6.2` orchestration merge/rerank policy |
| 082 | 2026-03-04 | Completed E5.6 task T5.6.2 and activated T5.6.3 | Added orchestration policy controls for graph traversal depth and merge/rerank weighting (`GRAPH_TRAVERSAL_DEPTH`, `HYBRID_VECTOR_WEIGHT`, `HYBRID_GRAPH_WEIGHT`) in settings, injected policy into retrieval filters from orchestrator, and updated hybrid retriever to apply policy-aware traversal/reranking with tests | Implement `T5.6.3` citation schema enforcement and tests |
| 083 | 2026-03-04 | Completed E5.6 task T5.6.3 and activated T5.6.4 | Added citation schema formatter in `agent/orchestrator/citations.py`, extended retrieval hit metadata contract (`source_file`, `page`, `section`, `chunk_id`), and enforced citation output block in hybrid-mode orchestrator responses; validated with `python -m unittest tests.test_graph_client tests.test_graph_schema tests.test_graph_relations tests.test_graph_ingest tests.test_citations tests.test_retriever tests.test_retrieval_filters tests.test_orchestrator tests.test_config_prompts tests.test_qdrant_ingest tests.test_entities tests.test_models tests.test_cli tests.test_ingest_helpers -v` (OK) | Implement `T5.6.4` GitNexus integration and source linking |
| 084 | 2026-03-04 | Completed E5.6 task T5.6.4 and activated T5.6.5 | Added GitNexus integration adapter (`knowledge/graph/gitnexus.py`) with graph payload + source-link mapping, added API endpoint `GET /graph/nexus` in `api/app.py`, and added tests (`tests.test_gitnexus`, `tests.test_api_engine_endpoints`) with config validation updates; validated with `python -m unittest tests.test_graph_client tests.test_graph_schema tests.test_graph_relations tests.test_graph_ingest tests.test_gitnexus tests.test_citations tests.test_retriever tests.test_retrieval_filters tests.test_orchestrator tests.test_config_prompts tests.test_qdrant_ingest tests.test_entities tests.test_models tests.test_cli tests.test_ingest_helpers tests.test_api_engine_endpoints tests.test_api_openai_adapter tests.test_api_config_controls -v` (OK) | Implement `T5.6.5` API/CLI controls for Graph-RAG visualization hooks |
| 085 | 2026-03-04 | Completed E5.6 task T5.6.5 and activated T5.6.6 | Added Graph-RAG/visualization control hooks in CLI (`run.py` + `chat_loop`) and API (`api/app.py`) to pass retrieval-mode and graph policy controls into request filters, plus tests for CLI/API control propagation | Update docs/runbook for Graph-RAG + GitNexus setup and troubleshooting (`T5.6.6`) |
| 086 | 2026-03-05 | Added retrieval quality hardening extension to backlog/tracker | Added Phase P6 / Epic E6.1 with tasks `T6.1.1`-`T6.1.TEST`; updated planned effort totals and phase/epic status tables | Start implementation at `T6.1.1` |
| 087 | 2026-03-05 | Completed `T6.1.1` startup guard implementation | Added startup checks for fallback embeddings and semantic dependency readiness (`config/settings.py`), made ingest startup validation respect CLI chunking flags (`run.py`), updated `.env.example`, and added validation tests | Proceed with `T6.1.2` semantic rechunking refactor |
| 088 | 2026-03-05 | Completed `T6.1.2` semantic grouping refactor | Added semantic pre-grouping over page/chapter structural groups before semantic rechunking, expanded PDF structure tests, and validated reduced short-fragment chunks on primary PDF | Proceed with `T6.1.3` chunk quality filters |
| 089 | 2026-03-05 | Completed `T6.1.3` chunk quality filtering | Added ingest-time chunk quality filtering (`min chars/words`) with list-aware exceptions and config wiring, plus regression tests for filtered fragments vs retained list chunks | Proceed with `T6.1.4` retrieval rerank and confidence hardening |
| 090 | 2026-03-05 | Completed `T6.1.4` retrieval rerank and confidence hardening | Added query-overlap rerank in retriever, added rerank config controls, tightened fallback-embedding low-confidence gate in orchestrator, and expanded retriever/orchestrator config tests | Proceed with `T6.1.5` quality diagnostics report |
| 091 | 2026-03-05 | Completed `T6.1.5` quality diagnostics report | Added chunk/retrieval diagnostics builder (`rag/retrieval/quality_report.py`), wired optional ingest report output flags in CLI, and validated with quality/CLI/ingest/config test suite | Proceed with `T6.1.TEST` final regression and benchmark evidence |
| 092 | 2026-03-05 | Completed `T6.1.TEST` and closed P6 | Added benchmark artifact `docs/p6-retrieval-quality-report.md`, executed full P6 regression suite (64 tests, OK), and closed Epic E6.1 / Phase P6 with tracker roll-up updates | Backlog scope complete |
| 093 | 2026-03-05 | Added new backlog phase P7 from `rag_improvements` requirements | Extended `docs/backlog.md` with Phase P7 / Epic E7.1 and task estimates; synchronized tracker totals, phase/epic status tables, and active task board | Start `T7.1.1` baseline probe report |
| 094 | 2026-03-05 | Completed E7.1 implementation and test gate | Added two-column PDF extraction/reflow and line normalization, keyword fallback retrieval with confidence trigger, retrieval provenance labels, quality-report keyword chunk probes + CLI options, and baseline artifacts (`docs/p7-recall-baseline.md`, `.json`); validated with `python -m unittest -v` (158 tests OK) | Backlog scope complete |
| 095 | 2026-03-09 | Added new backlog phase P8 from `text_extraction` requirements | Extended `docs/backlog.md` with Phase P8 / Epic E8.1 and task estimates; synchronized tracker totals, phase/epic status tables, planned-task register, and active task board | Start `T8.1.1` extraction contract and prompt policy |
| 096 | 2026-03-09 | Completed `T8.1.1` extraction contract and prompt policy | Added `docs/p8-text-extraction-contract.md` covering input/output contracts, normalization policy, LLM prompt constraints, error handling, and 300+ page scalability expectations | Start `T8.1.2` PyMuPDF extraction implementation |
| 097 | 2026-03-09 | Completed `T8.1.2` PyMuPDF page iterator and extraction range support | Added `iter_pdf_pages_with_pymupdf` in `rag/chunking/load_documents.py` with default `start_page=6`, optional `end_page`, strict validation, and normalized page-by-page output; validated with `python -m unittest tests.test_pdf_structure -v` (14 tests OK) | Start `T8.1.3` line normalization/preservation heuristics |
| 098 | 2026-03-09 | Completed `T8.1.3` pre-LLM normalization heuristics | Added `normalize_page_text_for_markdown_llm` with paragraph-aware merge logic, dehyphenation, and heading/list preservation; validated via `python -m unittest tests.test_pdf_structure -v` (17 tests OK) | Start `T8.1.4` LLM cleanup integration |
| 099 | 2026-03-09 | Completed `T8.1.4` page-level LLM cleanup router integration | Added `llm_cleanup_pdf_page` in `agent/reasoning/llm_router.py`, added markdown-cleanup prompt helpers in `config/prompts.py`, and exported via `llm_hub/router.py`; validated with `python -m unittest tests.test_llm_router tests.test_config_prompts -v` (29 tests OK) | Start `T8.1.5` output writer and document concatenation |
| 100 | 2026-03-09 | Completed `T8.1.5` markdown output writing and final document concatenation helpers | Added `write_page_markdown` and `concatenate_page_markdown_files` in `rag/chunking/load_documents.py` for `page_{number}.md` outputs and `document.md` merge with stable ordering and separators; validated via `python -m unittest tests.test_pdf_structure -v` (20 tests OK) | Start `T8.1.6` CLI/config wiring |
| 101 | 2026-03-09 | Completed `T8.1.6` CLI/config controls and extraction command wiring | Added `extract-markdown` command in `run.py`, extraction orchestrator helper `extract_pdf_to_markdown` in `rag/chunking/load_documents.py`, and startup validation extension in `config/settings.py` for extract flow; validated with `python -m unittest tests.test_cli tests.test_pdf_structure tests.test_config_prompts -v` (50 tests OK) | Start `T8.1.TEST` full extraction test gate |
| 102 | 2026-03-09 | Completed `T8.1.TEST` and closed Phase P8 | Added large-page-range batching regression test and validated extraction-related suite (`tests.test_llm_router`, `tests.test_pdf_structure`, `tests.test_cli`, `tests.test_config_prompts`) with `57` passing tests; closed `E8.1` and `P8` | Backlog scope complete |
| 103 | 2026-03-28 | Applied scoped refactor to `agent/orchestrator` | Added folder-local helper extraction (`common.py`), docstrings, named constants, and logged translation failures in `agent/orchestrator/*`; validated with `python -m unittest tests.test_orchestrator tests.test_citations -v` (11 tests OK) | Continue code-quality maintenance on adjacent runtime folders |
| 104 | 2026-03-28 | Fixed HTTP dependency warning in local runtime | Pinned `chardet<6` in `requirements.txt` and updated the project venv from `chardet 7.0.1` to `5.2.0`, removing the `RequestsDependencyWarning` on `requests` import | Continue folder-by-folder maintenance refactor |
| 105 | 2026-03-28 | Applied scoped refactor to `knowledge/qdrant` | Added folder-local helper extraction (`common.py`), docstrings, named constants, and collection lifecycle validation/logging in `knowledge/qdrant/*`; validated with `python -m unittest tests.test_qdrant_ingest tests.test_ingest_helpers -v` (12 tests OK) | Continue retrieval-layer maintenance refactor |
| 106 | 2026-03-28 | Applied scoped refactor to `rag/retrieval` | Added folder-local helper extraction (`common.py`), normalized retrieval-hit mapping, replaced magic constants, and tightened logging/docstrings across `rag/retrieval/*`; validated with `python -m unittest tests.test_retriever tests.test_retrieval_filters tests.test_quality_report tests.test_embeddings -v` (14 tests OK) | Continue configuration and chunking maintenance refactor |
| 107 | 2026-03-28 | Applied scoped refactor to `config` | Added shared env parsing helpers (`config/common.py`), reduced duplicated env parsing, added docstrings/constants, and preserved startup validation behavior across `config/*`; validated with `python -m unittest tests.test_config_prompts -v` (23 tests OK) | Finish maintenance refactor on chunking package |
| 108 | 2026-03-28 | Applied scoped refactor to `rag/chunking` | Added shared chunking helpers (`rag/chunking/common.py`), reused line/list/heading detection across chunking modules, added targeted docstrings/constants, and fixed `discover_markdown_paths()` to prefer `document.md`; validated with `python -m unittest tests.test_chunking tests.test_pdf_structure tests.test_load_documents -v` (43 tests OK) | Maintenance refactor sweep complete |
| 109 | 2026-03-28 | Applied scoped refactor to `agent/reasoning`, `agent/guardrail`, and `knowledge/entities` | Added docstrings and named constants, normalized provider/label literals, and improved explicit logging for dataset-load failures while preserving guardrail and extraction behavior; validated with `python -m unittest tests.test_llm_router tests.test_guardrail tests.test_entities -v` (16 tests OK) | Continue maintenance refactor on `knowledge/graph`, `api`, `models`, and `agent/evaluation` |
| 110 | 2026-03-28 | Applied scoped refactor to `knowledge/graph`, `api`, `models`, and `agent/evaluation` | Added named constants/docstrings, extracted graph query constant, replaced silent `except Exception` in GitNexus with logged exception handling, and normalized API literal usage while preserving endpoint behavior; validated with `python -m unittest tests.test_gitnexus tests.test_api_engine_endpoints tests.test_api_openai_adapter tests.test_api_config_controls tests.test_models tests.test_evaluator -v` (31 tests OK) | Maintenance refactor continued; optional follow-up: `agent/evaluation/benchmark.py` deep cleanup |
| 111 | 2026-03-28 | Applied deep refactor to `agent/evaluation/benchmark.py` | Added module/function docstrings, consolidated magic literals into constants, extracted repeated question-type/status parsing into helpers, and kept benchmark scoring/rejection behavior unchanged; validated with `python -m unittest tests.test_benchmark tests.test_evaluator -v` (35 tests OK) | Maintenance refactor sweep complete |
| 112 | 2026-03-28 | Deduplicated shared text normalization and graph row mapping helpers | Added shared normalization helper (`models/text_normalization.py`) used by guardrail/entities; added shared graph result mapper (`knowledge/graph/common.py`) used by retriever/GitNexus; validated with `python -m unittest tests.test_guardrail tests.test_entities tests.test_retriever tests.test_retrieval_filters tests.test_gitnexus -v` (19 tests OK) | Maintenance refactor sweep complete |
| 113 | 2026-03-28 | Synchronized runtime imports with dependency manifest | Updated `requirements.txt` to include direct runtime imports (`httpx`, `ollama`, `PyMuPDF`) and removed duplicate `python-dotenv` entry | Dependency manifest aligned with current code imports |
| 114 | 2026-04-16 | Upgraded evaluator with failure taxonomy and adaptive retry strategy while keeping benchmark module separate | Added evaluator modules (`failure_taxonomy`, `heuristics`, `adaptive_prompt`, `llm_judge`), expanded `EvaluatorResult` + `EvalConfig`, wired orchestrator retry flow to use `adaptive_prompt` and `retry_strategy` (`switch_llm` vs `adjust_prompt`), and fixed API eval dependency import to keep benchmark wiring functional (`api/dependencies.py` now imports `agent.benchmarking.benchmark`); validated with `python -m unittest tests.test_evaluator tests.test_orchestrator tests.test_models -v` (24 tests OK) and `python -m unittest tests.test_api_engine_endpoints tests.test_api_openai_adapter tests.test_api_config_controls -v` (15 tests OK) | Optional next step: tune penalty weights/thresholds with real query logs or benchmark-style probes |

## Known Risks and Blockers

- Current environment restrictions prevent downloading external model artifacts during runtime checks.
- Several modules are placeholders/empty and will require first implementation before integration tests can pass.
- Legacy compatibility shims remain until planned removal at end of Phase 2, which adds temporary maintenance overhead.
- LlamaIndex, KuzuDB, and GitNexus integration may require new dependencies and compatibility validation with existing runtime/container setup.
- PDF parsing quality may vary by source document formatting; OCR fallback may be required for some pages.
