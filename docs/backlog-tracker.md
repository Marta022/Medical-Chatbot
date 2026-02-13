# Backlog Tracker

Last updated: 2026-02-13  
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
| Planned effort | 238h |
| Completed effort | 88h |
| In-progress effort | 0h |
| Remaining effort | 150h |
| Overall completion | 37% |

## Phase Progress

| Phase | Planned (h) | Done (h) | In Progress (h) | Remaining (h) | Status |
| --- | --- | --- | --- | --- | --- |
| P0 Product Definition and Planning | 28 | 28 | 0 | 0 | DONE |
| P1 Architecture and Codebase Reorganization | 60 | 60 | 0 | 0 | DONE |
| P2 Core Orchestration and Safety Pipeline | 50 | 0 | 0 | 50 | TODO |
| P3 Code Quality and Observability | 40 | 0 | 0 | 40 | TODO |
| P4 Runtime and Delivery | 60 | 0 | 0 | 60 | TODO |

## Epic Progress

| Epic ID | Epic | Planned (h) | Done (h) | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| E0.1 | PRD Authoring and Scope Baseline | 16 | 16 | DONE | PRD baseline completed in `docs/prd.md` with requirement traceability |
| E0.2 | Backlog Governance and Tracker Setup | 12 | 12 | DONE | Risk-buffer model and governance dry-run completed |
| E1.1 | Repository Restructuring to Target Layout | 24 | 24 | DONE | Shims finalized, dataset move complete, import/path validation complete |
| E1.2 | Unified CLI Entrypoint | 10 | 10 | DONE | README examples and CLI smoke tests completed |
| E1.3 | Configuration and Prompt Normalization | 10 | 10 | DONE | Prompt centralization + startup validation + config tests completed |
| E1.4 | Domain Models and Typed Contracts | 16 | 16 | DONE | Typed flow refactor + serde + guidelines completed |
| E2.1 | Orchestrator and Evaluator Retry Loop | 20 | 0 | TODO | Includes mandatory epic test task |
| E2.2 | Guardrail Hardening | 12 | 0 | TODO | Includes mandatory epic test task |
| E2.3 | RAG and Ingestion Robustness | 18 | 0 | TODO | Includes mandatory epic test task |
| E3.1 | Structured Logging | 12 | 0 | TODO | Includes mandatory epic test task |
| E3.2 | PEP8 Refactor and Static Checks | 14 | 0 | TODO | Includes mandatory epic test task |
| E3.3 | Automated Testing and Quality Gates | 14 | 0 | TODO | Includes mandatory epic test task |
| E4.1 | Application Containerization | 10 | 0 | TODO | Includes mandatory epic test task |
| E4.2 | Docker Compose Topology | 16 | 0 | TODO | Includes mandatory epic test task |
| E4.3 | Operations and Release Documentation | 14 | 0 | TODO | Includes mandatory epic test task |
| E4.4 | REST API and OpenWebUI Integration | 20 | 0 | TODO | New epic for engine REST and OpenWebUI compatibility |

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

## Active Task Board

Use this section for current work only (max 10 items at a time).

| Task ID | Task | Estimate (h) | Actual (h) | Owner | Status | Start | End | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T2.1.1 | Implement orchestrator class with explicit step pipeline | 4 | 0 | TBD | TODO |  |  | Start of Phase 2 |
| T2.1.2 | Integrate evaluator call after LLM response | 3 | 0 | TBD | TODO |  |  |  |
| T2.1.3 | Implement retry policy: adjusted prompt and provider fallback | 3 | 0 | TBD | TODO |  |  |  |
| T2.1.4 | Implement evaluator scoring (grounding, safety, language compliance) | 4 | 0 | TBD | TODO |  |  |  |
| T2.1.5 | Add evaluator config model in `config/eval_config.py` | 2 | 0 | TBD | TODO |  |  |  |
| T2.1.6 | Add evaluator result schema and structured logs | 2 | 0 | TBD | TODO |  |  |  |
| T2.1.TEST | Tests for orchestrator + evaluator retry loop | 2 | 0 | TBD | TODO |  |  | Mandatory epic test task |
| T2.2.1 | Expand and test emergency/unsafe phrase coverage | 2 | 0 | TBD | TODO |  |  |  |
| T2.2.2 | Add guardrail reason codes and confidence fields | 2 | 0 | TBD | TODO |  |  |  |
| T2.2.3 | Add fallback for LLM guardrail unavailability | 2 | 0 | TBD | TODO |  |  |  |

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

## Known Risks and Blockers

- Current environment restrictions prevent downloading external model artifacts during runtime checks.
- Several modules are placeholders/empty and will require first implementation before integration tests can pass.
- Legacy compatibility shims remain until planned removal at end of Phase 2, which adds temporary maintenance overhead.
