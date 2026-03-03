# Backlog Tracker

Last updated: 2026-03-01  
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
| Completed effort | 238h |
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

## Known Risks and Blockers

- Current environment restrictions prevent downloading external model artifacts during runtime checks.
- Several modules are placeholders/empty and will require first implementation before integration tests can pass.
- Legacy compatibility shims remain until planned removal at end of Phase 2, which adds temporary maintenance overhead.
