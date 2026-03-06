# Medical Chatbot Backlog

Date: 2026-03-05  
Version: 4.2  
Estimation unit: engineering hours (`h`)  
Source inputs: `docs/raw_idea/licenta_title.txt`, `docs/raw_idea/raw_backlog.txt`, `docs/raw_idea/new_backlog.txt`, repository inspection

## Goal of This Backlog

This backlog is written so a new developer can resume work without deep project discovery.

What this document provides:
- phase and epic sequencing
- technical scope per epic
- expected deliverables
- dependencies
- explicit acceptance criteria
- effort estimates with subtotals

## Current State Baseline

Key findings from repository review:
- `agents/main_agent.py` has a basic loop but does not implement evaluator-driven retry from `agents.md`.
- `evaluation/evaluator.py`, `evaluation/benchmark.py`, `config/eval_config.py`, `config/prompts.py`, and `llm_hub/anthropic_client.py` are empty.
- `app.py` and `agents/main_agent.py` both behave like entrypoints; no unified CLI exists.
- runtime modules still use direct `print(...)` instead of structured logging.
- `ingestion/ingest_vectordb.py` imports `ensure_collection`, but `vector_db/qdrant_client.py` does not provide it.
- Docker assets now exist (`Dockerfile`, `docker-compose.yml`), but container smoke tests are currently blocked by Docker layer extraction/cache corruption in the local environment.

## Execution Status Snapshot (2026-03-05)

- Overall status: `DONE` (Phase P7 completed)
- Active phase: `P7` (Query Recall and Lexical Fallback)
- Current active task: `None` (all planned backlog tasks completed)
- Current blocker: none
- Source of truth: `docs/backlog-tracker.md`

## Mandatory Execution Rules

- Do not start an epic unless dependencies are complete or explicitly parallel-safe.
- Every task completion must update `docs/backlog-tracker.md`.
- Every epic must end with evidence: changed files, validation commands, known risks.
- Every epic must contain and complete a `*.TEST` task before epic status becomes `DONE`.
- If blocked, mark `BLOCKED`, include reason, and include concrete unblock proposal.

## Epic-Level Test Gate (Mandatory)

For each epic:
- implement or update tests in the same epic, not postponed to a later phase
- include at least one positive path and one negative/edge path
- run relevant tests before marking epic `DONE`
- record test command and result in `docs/backlog-tracker.md`

## Estimation and Risk Buffer Policy

Use this model for all remaining backlog items:
- `Base Estimate`: implementation hours without uncertainty buffer.
- `Risk Class`: `LOW`, `MEDIUM`, `HIGH`.
- `Risk Buffer`:
- `LOW`: `+10%`
- `MEDIUM`: `+20%`
- `HIGH`: `+35%`
- `Buffered Estimate` = `Base Estimate + Risk Buffer`.

Calibration rules:
- New component or external integration defaults to `MEDIUM` unless evidence suggests otherwise.
- Any dependency on third-party runtime services (model APIs, Docker networking, vector store) is at least `MEDIUM`.
- Tasks with unclear requirements stay `BLOCKED` until scope is clarified; do not absorb ambiguity by inflating estimates.
- If actual effort exceeds buffered estimate by `>20%`, log cause in tracker and split follow-up into a new task.

## Python Modeling Rule (Mandatory)

All core objects must be modeled as Python types (for example dataclasses or Pydantic models), not ad-hoc dictionaries embedded in business logic.

Minimum modeled objects:
- user query request
- guardrail result
- retrieval hit/context item
- LLM request/response envelope
- evaluator result
- API request/response payloads

## Target Architecture Map

| Area | Current | Target |
| --- | --- | --- |
| Agent | `agents/main_agent.py` | `agent/orchestrator`, `agent/guardrail`, `agent/evaluation`, `agent/reasoning` |
| Retrieval | `rag/retriever.py` | `rag/retrieval/*` |
| Chunking | implicit in ingestion | `rag/chunking/*` |
| Knowledge store | `vector_db/qdrant_client.py` | `knowledge/qdrant/*` |
| Dataset | `data/disease_database.json`, `data/dataset - Sheet1.csv` | `data/dataset/*` |
| Config | mixed env and prompt loading | centralized in `config/*` |
| Entrypoint | loops in `app.py`, `agents/main_agent.py` | CLI entrypoint in `main.py` or `run.py` |
| API | not available | REST API with engine endpoints + OpenAI-compatible adapter for OpenWebUI |

## Global Definition of Done

These conditions apply to all implementation epics:
- touched code is PEP8-compliant
- no new direct `print(...)` in runtime modules
- tests for changed behavior are added/updated and passing
- docs are updated for behavior/config changes
- tracker is updated with actual hours and validation evidence

## Phase Summary

| Phase | Name | Epic Count | Subtotal (h) |
| --- | --- | --- | --- |
| P0 | Product Definition and Planning | 2 | 28 |
| P1 | Architecture and Codebase Reorganization | 4 | 60 |
| P2 | Core Orchestration and Safety Pipeline | 3 | 50 |
| P3 | Code Quality and Observability | 3 | 40 |
| P4 | Runtime and Delivery | 4 | 60 |
| P5 | Semantic Knowledge and Graph-RAG Expansion | 6 | 134 |
| P6 | Retrieval Quality Hardening | 1 | 26 |
| P7 | Query Recall and Lexical Fallback | 1 | 22 |
|  | **Grand Total** | **24** | **420** |

## Phase P0: Product Definition and Planning (28h)

Goal: turn thesis intent and raw notes into executable, traceable implementation plan.

### Epic E0.1: PRD Authoring and Scope Baseline (16h)

Technical description:
- create `docs/prd.md` with product scope, user flows, constraints, metrics, and acceptance targets
- map requirements to components and backlog items

Primary files:
- `docs/prd.md` (new)
- `docs/backlog.md`

Deliverables:
- PRD with versioning and changelog
- requirement-to-component matrix
- requirement-to-backlog mapping table

Dependencies:
- none

Acceptance criteria:
- `docs/prd.md` exists and contains goals, non-goals, constraints, architecture, risks, rollout
- each major requirement maps to at least one backlog task ID
- measurable success metrics are defined
- `T0.1.TEST` completed with validation checklist tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S0.1 | T0.1.1 | Extract requirements from `docs/raw_idea/*` and normalize terminology | Requirement inventory table | 2 |
| S0.1 | T0.1.2 | Draft PRD core sections: problem, goals, users, scope, out-of-scope | PRD draft v0.1 | 4 |
| S0.1 | T0.1.3 | Define functional and non-functional requirements | NFR section with thresholds | 2 |
| S0.2 | T0.1.4 | Map PRD requirements to architecture modules and ownership | Traceability matrix | 2 |
| S0.2 | T0.1.5 | Review and revise PRD using advisor checklist | PRD v1.0 review notes | 3 |
| S0.2 | T0.1.6 | Baseline PRD in `docs/prd.md` | Approved PRD v1.0 | 1 |
| S0.2 | T0.1.TEST | Validate PRD completeness and link integrity | PRD validation checklist | 2 |
|  |  | **Epic subtotal** |  | **16** |

### Epic E0.2: Backlog Governance and Tracker Setup (12h)

Technical description:
- define ID, status, effort, cadence, and changelog standards
- ensure execution is trackable by any new developer

Primary files:
- `docs/backlog.md`
- `docs/backlog-tracker.md`

Deliverables:
- governance rules and status lifecycle
- estimation policy
- tracking cadence and DoR/DoD standards

Dependencies:
- E0.1 preferred

Acceptance criteria:
- tracker supports `TODO`, `IN_PROGRESS`, `BLOCKED`, `DONE`
- each task has unique ID and traceable state
- work log template exists and is used
- `T0.2.TEST` completed with tracker workflow dry-run

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S0.3 | T0.2.1 | Define backlog ID convention and status lifecycle | Governance section | 2 |
| S0.3 | T0.2.2 | Define tracker metrics (planned, actual, blocked, carryover) | Metrics schema | 2 |
| S0.4 | T0.2.3 | Define update cadence and DoR/DoD gates | Cadence + DoR/DoD | 2 |
| S0.4 | T0.2.4 | Calibrate estimates and risk buffer model | Estimation policy | 2 |
| S0.4 | T0.2.5 | Define changelog procedure for every step | Logging procedure | 2 |
| S0.4 | T0.2.TEST | Dry-run tracker lifecycle on sample task | Tracker dry-run evidence | 2 |
|  |  | **Epic subtotal** |  | **12** |

## Phase P1: Architecture and Codebase Reorganization (60h)

Goal: align codebase to target structure, typed contracts, and deterministic startup.

### Epic E1.1: Repository Restructuring to Target Layout (24h)

Technical description:
- move modules to requested package layout
- split retrieval and chunking responsibilities
- move dataset and knowledge-store code to dedicated domains

Primary files:
- `agents/*` -> `agent/*`
- `vector_db/*` -> `knowledge/qdrant/*`
- `rag/retriever.py` -> `rag/retrieval/*`
- `ingestion/*`
- `data/*` -> `data/dataset/*`

Deliverables:
- new folder structure
- updated imports
- migration map (old path -> new path)

Dependencies:
- E0.1

Acceptance criteria:
- no import errors due to moved modules
- dataset ingestion works with new paths
- compatibility shims documented if temporarily used
- `T1.1.TEST` completed with import/smoke checks

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S1.1 | T1.1.1 | Create target package tree and migration plan | Migration plan | 2 |
| S1.1 | T1.1.2 | Move first-party modules and fix imports | Refactored package tree | 4 |
| S1.1 | T1.1.3 | Add temporary compatibility shims where needed | Shim modules + deprecation notes | 2 |
| S1.2 | T1.1.4 | Move dataset files to `data/dataset` and update ingestion paths | Updated dataset location and loader paths | 2 |
| S1.2 | T1.1.5 | Move Qdrant client code to `knowledge/qdrant` | Knowledge-store package | 3 |
| S1.2 | T1.1.6 | Validate package imports after migration | Import validation notes | 3 |
| S1.3 | T1.1.7 | Split RAG into explicit `chunking` and `retrieval` modules | RAG subpackages | 3 |
| S1.3 | T1.1.8 | Refactor ingestion to use chunking abstraction | Updated ingestion pipeline | 3 |
| S1.3 | T1.1.TEST | Run structure smoke tests and import checks | Structure smoke test evidence | 2 |
|  |  | **Epic subtotal** |  | **24** |

### Epic E1.2: Unified CLI Entrypoint (10h)

Technical description:
- replace ad-hoc loops with one CLI
- expose `chat`, `ingest`, `eval` modes

Primary files:
- `main.py` or `run.py`
- `app.py`
- `agents/main_agent.py` (or migrated equivalent)

Deliverables:
- CLI entrypoint
- command handlers
- usage docs

Dependencies:
- E1.1

Acceptance criteria:
- `python <entrypoint> --help` lists commands
- each command starts intended flow without source edits
- old entrypoints removed or delegate to CLI
- `T1.2.TEST` completed with command smoke tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S1.4 | T1.2.1 | Implement CLI entrypoint with subcommands | CLI module | 3 |
| S1.4 | T1.2.2 | Add runtime modes: `chat`, `ingest`, `eval` | Command handlers | 3 |
| S1.4 | T1.2.3 | Update usage docs and run examples | README CLI section | 2 |
| S1.4 | T1.2.TEST | CLI command smoke tests | CLI smoke test evidence | 2 |
|  |  | **Epic subtotal** |  | **10** |

### Epic E1.3: Configuration and Prompt Normalization (10h)

Technical description:
- centralize env parsing and prompt loading
- fail fast for missing required config

Primary files:
- `config/settings.py`
- `config/prompts.py`
- `llm.txt`

Deliverables:
- normalized config schema
- prompt registry
- startup config validator

Dependencies:
- E1.2 preferred

Acceptance criteria:
- missing required env vars fail with clear errors
- prompt strings are not scattered across runtime code
- provider/config switches do not require code edits
- `T1.3.TEST` completed with config validation tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S1.5 | T1.3.1 | Centralize environment config parsing and defaults | Config schema module | 2 |
| S1.5 | T1.3.2 | Populate `config/prompts.py` and move prompt literals | Prompt registry | 3 |
| S1.5 | T1.3.3 | Add startup checks for required secrets/config | Config validator | 3 |
| S1.5 | T1.3.TEST | Config and prompt load tests | Config test evidence | 2 |
|  |  | **Epic subtotal** |  | **10** |

### Epic E1.4: Domain Models and Typed Contracts (16h)

Technical description:
- replace hardcoded dict-based objects with explicit Python models
- define typed contracts for orchestration, guardrails, retrieval, evaluation, and API payloads

Primary files:
- `models/*` (new package, or equivalent target structure)
- orchestrator, guardrail, rag, evaluation modules
- future API layer models

Deliverables:
- shared model definitions
- model mapping from current dict payloads
- serialization helpers and validation

Dependencies:
- E1.1

Acceptance criteria:
- critical runtime objects are represented as typed models
- functions no longer rely on implicit dict keys for core logic
- model validation errors are explicit and handled
- `T1.4.TEST` completed with model serialization/validation tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S1.6 | T1.4.1 | Inventory hardcoded objects currently passed as dicts | Object inventory matrix | 2 |
| S1.6 | T1.4.2 | Define shared models for query, guardrail, retrieval, evaluator, llm envelopes | Model package | 4 |
| S1.6 | T1.4.3 | Refactor core modules to consume typed models | Refactored typed flows | 4 |
| S1.6 | T1.4.4 | Add serialization/deserialization helpers | Serialization layer | 2 |
| S1.6 | T1.4.5 | Document model ownership and usage guidelines | Model guidelines doc section | 2 |
| S1.6 | T1.4.TEST | Add tests for model validation and mapping | Model test evidence | 2 |
|  |  | **Epic subtotal** |  | **16** |

## Phase P2: Core Orchestration and Safety Pipeline (50h)

Goal: implement complete main-agent lifecycle defined in `agents.md`.

### Epic E2.1: Orchestrator and Evaluator Retry Loop (20h)

Technical description:
- implement full orchestrator sequence:
- guardrail check
- retrieval decision and context fetch
- prompt construction
- LLM call
- evaluator decision
- retry with adjusted prompt or provider fallback

Primary files:
- `agent/orchestrator/*`
- `evaluation/evaluator.py`
- `config/eval_config.py`
- `llm_hub/router.py`

Deliverables:
- orchestrator implementation
- evaluator score contract
- retry/fallback policy implementation

Dependencies:
- E1.1, E1.3, E1.4

Acceptance criteria:
- one query execution logs each pipeline step and output
- evaluator can reject a response and trigger retry path
- provider fallback works when configured
- response includes provenance fields (`provider`, `retries`, `guardrail_status`)
- `T2.1.TEST` completed with happy/retry/fallback tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S2.1 | T2.1.1 | Implement orchestrator class with explicit step pipeline | Orchestrator module | 4 |
| S2.1 | T2.1.2 | Integrate evaluator call after LLM response | Evaluator integration | 3 |
| S2.1 | T2.1.3 | Implement retry policy: adjusted prompt and provider fallback | Retry/fallback module | 3 |
| S2.2 | T2.1.4 | Implement evaluator scoring (grounding, safety, language compliance) | Scoring logic | 4 |
| S2.2 | T2.1.5 | Add evaluator config model in `config/eval_config.py` | Eval config schema | 2 |
| S2.2 | T2.1.6 | Add evaluator result schema and structured logs | Evaluator result contract | 2 |
| S2.2 | T2.1.TEST | Tests for orchestrator + evaluator retry loop | Orchestrator test evidence | 2 |
|  |  | **Epic subtotal** |  | **20** |

### Epic E2.2: Guardrail Hardening (12h)

Technical description:
- improve keyword + optional LLM guardrail behavior
- expose reason codes/confidence for auditability

Primary files:
- `guardrails/rules.py` or migrated equivalent
- `guardrails/llm_guardrail.py`

Deliverables:
- enriched guardrail outputs
- deterministic fallback behavior
- standardized blocked-response templates

Dependencies:
- E2.1

Acceptance criteria:
- guardrail result includes `is_valid`, `is_emergency`, `is_unsafe`, `reason_code`
- emergency/unsafe scenarios covered by automated tests
- LLM guardrail outage falls back safely to deterministic rules
- `T2.2.TEST` completed with coverage on emergency and unsafe flows

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S2.3 | T2.2.1 | Expand and test emergency/unsafe phrase coverage | Updated phrase sets | 2 |
| S2.3 | T2.2.2 | Add guardrail reason codes and confidence fields | Enriched guardrail schema | 2 |
| S2.3 | T2.2.3 | Add fallback for LLM guardrail unavailability | Fallback path | 2 |
| S2.4 | T2.2.4 | Standardize emergency/unsafe message templates | Message template module | 2 |
| S2.4 | T2.2.5 | Add safety event logging | Safety event logs | 2 |
| S2.4 | T2.2.TEST | Tests for rule-based and LLM-assisted guardrails | Guardrail test evidence | 2 |
|  |  | **Epic subtotal** |  | **12** |

### Epic E2.3: RAG and Ingestion Robustness (18h)

Technical description:
- fix Qdrant collection lifecycle and ingestion reliability
- improve retrieval confidence handling and filters

Primary files:
- `vector_db/qdrant_client.py` or `knowledge/qdrant/*`
- `rag/retriever.py` or `rag/retrieval/*`
- `ingestion/load_documents.py`
- `ingestion/ingest_vectordb.py`

Deliverables:
- `ensure_collection` implementation
- retrieval filter + confidence gate support
- ingestion validation and dedup behavior

Dependencies:
- E1.1 and E1.4

Acceptance criteria:
- ingestion no longer fails because of missing `ensure_collection`
- low-confidence retrieval can trigger safe fallback
- CSV/JSON validation errors are explicit
- repeated ingestion does not create uncontrolled duplicates
- `T2.3.TEST` completed with ingestion/retrieval tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S2.5 | T2.3.1 | Implement Qdrant collection lifecycle (`ensure_collection`) | Collection lifecycle functions | 3 |
| S2.5 | T2.3.2 | Add retrieval filters and dynamic `top_k` support | Retrieval config support | 3 |
| S2.5 | T2.3.3 | Add low-confidence gate with safe fallback | Confidence gate logic | 3 |
| S2.6 | T2.3.4 | Add chunking strategies (`sentence/window/section`) | Chunking strategy module | 3 |
| S2.6 | T2.3.5 | Add CSV/JSON schema validation and error handling | Input validation layer | 2 |
| S2.6 | T2.3.6 | Add idempotent ingestion and duplicate detection | Dedup support | 2 |
| S2.6 | T2.3.TEST | Integration tests for ingestion and retrieval behavior | RAG test evidence | 2 |
|  |  | **Epic subtotal** |  | **18** |

## Phase P3: Code Quality and Observability (40h)

Goal: make system maintainable, diagnosable, and quality-gated.

### Epic E3.1: Structured Logging (12h)

Technical description:
- implement centralized logging bootstrap
- replace prints with level-based logs
- add correlation ID support

Primary files:
- logging setup module
- runtime modules (orchestrator, ingestion, guardrails, CLI)

Deliverables:
- standard log format
- consistent logger usage
- correlation ID propagation

Dependencies:
- E1.2, E1.4

Acceptance criteria:
- no direct `print(...)` remains in runtime paths
- logs include timestamp, level, module, correlation ID
- errors include meaningful context and traceback
- `T3.1.TEST` completed with logging behavior checks

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S3.1 | T3.1.1 | Create centralized logging configuration | Logger bootstrap module | 3 |
| S3.1 | T3.1.2 | Replace `print` usage in first-party modules | Runtime logging refactor | 4 |
| S3.1 | T3.1.3 | Add correlation ID per request/session | Correlation ID helper | 3 |
| S3.1 | T3.1.TEST | Tests for logging config and correlation propagation | Logging test evidence | 2 |
|  |  | **Epic subtotal** |  | **12** |

### Epic E3.2: PEP8 Refactor and Static Checks (14h)

Technical description:
- standardize style checks and formatting gates
- prevent regressions with pre-commit enforcement

Primary files:
- `pyproject.toml` and/or tool configs
- `.pre-commit-config.yaml`
- first-party Python modules

Deliverables:
- lint/format tool config
- style-compliant code
- pre-commit quality gate

Dependencies:
- P1/P2 core refactors stabilized

Acceptance criteria:
- chosen linter/formatter runs clean on first-party modules
- pre-commit executes lint + format checks
- exceptions are documented with rationale
- `T3.2.TEST` completed with lint/format CI-like run

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S3.2 | T3.2.1 | Add lint/format tooling configuration | Tooling config files | 3 |
| S3.2 | T3.2.2 | Refactor first-party modules for PEP8 compliance | PEP8-compliant modules | 5 |
| S3.2 | T3.2.3 | Add pre-commit hooks for style checks | `.pre-commit-config.yaml` | 2 |
| S3.2 | T3.2.4 | Resolve/document dead or empty modules | Dead code registry | 2 |
| S3.2 | T3.2.TEST | Execute lint/format gate and record baseline | Quality gate evidence | 2 |
|  |  | **Epic subtotal** |  | **14** |

### Epic E3.3: Automated Testing and Quality Gates (14h)

Technical description:
- create deterministic unit/integration tests for critical behavior
- enforce coverage threshold

Primary files:
- `tests/*`
- CI config (if present)
- orchestrator/guardrail/evaluator/rag modules

Deliverables:
- test suite for high-risk behavior
- coverage report and fail-under threshold

Dependencies:
- E2.1, E2.2, E2.3

Acceptance criteria:
- tests cover guardrail, evaluator, retry, and retrieval fallback behavior
- test command is documented and reproducible
- coverage threshold is enforced in local or CI gate
- `T3.3.TEST` completed by running full test suite

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S3.3 | T3.3.1 | Unit tests for guardrails and evaluator | Unit test modules | 4 |
| S3.3 | T3.3.2 | Integration tests for orchestration happy/retry paths | Integration tests | 4 |
| S3.3 | T3.3.3 | Mocked tests for retrieval and LLM providers | Mock fixtures/tests | 2 |
| S3.3 | T3.3.4 | Add coverage threshold and CI enforcement | Coverage + CI config | 2 |
| S3.3 | T3.3.TEST | Full suite run and baseline test report | Full test report | 2 |
|  |  | **Epic subtotal** |  | **14** |

## Phase P4: Runtime and Delivery (60h)

Goal: provide runnable containers, API integration, and release-ready documentation.

### Epic E4.1: Application Containerization (10h)

Technical description:
- package app into secure, reproducible image
- wire startup to unified CLI entrypoint

Primary files:
- `Dockerfile`
- `.dockerignore`

Deliverables:
- runnable image
- healthcheck
- non-root runtime

Dependencies:
- E1.2

Acceptance criteria:
- `docker build` succeeds from project root
- container starts without manual patching
- runtime user is non-root
- `T4.1.TEST` completed with container smoke test

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S4.1 | T4.1.1 | Add `Dockerfile` with slim runtime and non-root user | Dockerfile | 3 |
| S4.1 | T4.1.2 | Add `.dockerignore` and optimize dependency layers | .dockerignore + optimized layers | 2 |
| S4.1 | T4.1.3 | Add healthcheck and startup command | Healthcheck + entrypoint | 3 |
| S4.1 | T4.1.TEST | Build and run container smoke test | Container smoke evidence | 2 |
|  |  | **Epic subtotal** |  | **10** |

### Epic E4.2: Docker Compose Topology (16h)

Technical description:
- compose services as separate containers:
- `app`
- `qdrant` (from Docker Hub)
- `openwebui` (separate instance)

Primary files:
- `docker-compose.yml`
- `.env.example`

Deliverables:
- multi-service topology
- persistent volumes
- network wiring and service discovery

Dependencies:
- E4.1

Acceptance criteria:
- `docker compose up -d` starts `app`, `qdrant`, `openwebui`
- app reaches qdrant by compose service name
- qdrant data persists across restarts
- required env setup is documented
- `T4.2.TEST` completed with compose startup/shutdown checks

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S4.2 | T4.2.1 | Create `docker-compose.yml` with app/qdrant/openwebui | Compose file | 4 |
| S4.2 | T4.2.2 | Configure volumes, networks, and env wiring | Compose network + env config | 3 |
| S4.2 | T4.2.3 | Ensure app resolves qdrant and persistence works | Connectivity notes | 3 |
| S4.2 | T4.2.4 | Add optional profiles for provider integrations | Compose profile config | 2 |
| S4.2 | T4.2.5 | Validate compose startup/shutdown scenarios | Smoke checklist | 2 |
| S4.2 | T4.2.TEST | Compose integration tests and logs validation | Compose test evidence | 2 |
|  |  | **Epic subtotal** |  | **16** |

### Epic E4.3: Operations and Release Documentation (14h)

Technical description:
- write runbook for local, Docker, and test flows
- produce release/demo checklist and risk register

Primary files:
- `README.md`
- `docs/prd.md`
- `docs/*`

Deliverables:
- end-to-end runbook
- release checklist
- acceptance checklist mapped to PRD

Dependencies:
- E4.1, E4.2

Acceptance criteria:
- a new developer can run chat flow using docs only
- docs include troubleshooting for common failures
- release checklist includes guardrail/rag/evaluator/container verifications
- `T4.3.TEST` completed with docs walk-through validation

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S4.3 | T4.3.1 | Update README with CLI, ingestion, Docker flows | README runbook | 4 |
| S4.3 | T4.3.2 | Align `docs/prd.md` and architecture diagram with implementation | PRD + architecture sync | 3 |
| S4.3 | T4.3.3 | Add release/demo checklist and risk register | Release checklist | 3 |
| S4.3 | T4.3.4 | Add final acceptance checklist mapped to PRD | Acceptance mapping | 2 |
| S4.3 | T4.3.TEST | Perform docs walk-through validation | Docs validation evidence | 2 |
|  |  | **Epic subtotal** |  | **14** |

### Epic E4.4: REST API and OpenWebUI Integration (20h)

Technical description:
- expose engine capabilities through REST endpoints
- add OpenAI-compatible adapter endpoints so OpenWebUI can connect directly
- route API calls through orchestrator and typed models

Primary files:
- `api/*` (new package)
- `main.py` / CLI wiring
- `models/*`
- `docker-compose.yml` and docs for OpenWebUI connection

Deliverables:
- REST endpoints for engine operations
- OpenAI-compatible endpoints for OpenWebUI (`/v1/models`, `/v1/chat/completions`)
- API auth/config and request validation

Dependencies:
- E1.4, E2.1, E4.2

Acceptance criteria:
- API has health endpoint and engine endpoints callable via HTTP
- OpenWebUI can be configured to call this API through OpenAI-compatible routes
- API requests/ responses use typed models, not ad-hoc dict payloads
- endpoint errors return consistent HTTP status and JSON error schema
- `T4.4.TEST` completed with API integration tests (including OpenWebUI-compatible flow)

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S4.4 | T4.4.1 | Create API application skeleton and dependency wiring | API app scaffold | 4 |
| S4.4 | T4.4.2 | Implement engine endpoints (`/health`, `/chat`, `/ingest`, `/eval`) | Engine REST endpoints | 5 |
| S4.4 | T4.4.3 | Implement OpenAI-compatible adapter (`/v1/models`, `/v1/chat/completions`) | OpenWebUI-compatible adapter | 5 |
| S4.4 | T4.4.4 | Add API config for auth, limits, and environment controls | API config module | 2 |
| S4.4 | T4.4.5 | Update compose/docs for OpenWebUI -> API integration | Integration runbook section | 2 |
| S4.4 | T4.4.TEST | API integration tests and compatibility validation | API test evidence | 2 |
|  |  | **Epic subtotal** |  | **20** |

## Phase P5: Semantic Knowledge and Graph-RAG Expansion (134h)

Goal: move from simple chunk-and-retrieve to document-structured semantic retrieval with entity/relation graph augmentation and graph-aware citations.

### Epic E5.1: PDF Dataset Baseline and Structure Detection (16h)

Technical description:
- adopt medical PDF files from `data/dataset/*` as primary corpus
- inspect document structure (chapters, sections, titles, numbered lists, bullet lists)
- define metadata contract for downstream chunking and citation

Primary files:
- `data/dataset/*.pdf`
- `rag/chunking/load_documents.py`
- `models/contracts.py`
- `docs/*` (structure report)

Deliverables:
- PDF structure analysis artifact
- parser output schema with normalized metadata
- deterministic `chunk_id` specification

Dependencies:
- E2.3 completed

Acceptance criteria:
- parser identifies chapter/section/title/list boundaries for at least one main medical PDF
- output records include `source_file`, `page`, `chapter`, `section`, `chunk_id`
- malformed/low-text pages are logged and skipped safely
- `T5.1.TEST` completed with parser/metadata tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S5.1 | T5.1.1 | Inspect PDF layout and define extraction rules for headings/lists | PDF structure profile report | 4 |
| S5.1 | T5.1.2 | Implement PDF parser with page-aware structural signals | Structured page parser | 5 |
| S5.1 | T5.1.3 | Define and validate metadata schema including stable `chunk_id` rules | Typed metadata models | 3 |
| S5.1 | T5.1.4 | Add parser logging for unreadable pages and OCR edge cases | Parser diagnostics | 2 |
| S5.1 | T5.1.TEST | Parser and metadata unit tests | Test evidence for structure extraction | 2 |
|  |  | **Epic subtotal** |  | **16** |

### Epic E5.2: Semantic Chunking with LlamaIndex (22h)

Technical description:
- replace fixed heuristic chunking with semantic chunking using LlamaIndex
- align chunk boundaries to meaning and document structure
- preserve numbered and bulleted list integrity when context is semantically contiguous

Primary files:
- `rag/chunking/strategies.py`
- `rag/chunking/load_documents.py`
- `requirements.txt`
- `config/settings.py`

Deliverables:
- LlamaIndex-based semantic chunker
- fallback chunker for runtime degradation
- metadata-enriched chunk records

Dependencies:
- E5.1

Acceptance criteria:
- semantic chunking strategy selectable via config/CLI
- list continuity policy keeps related list items in same chunk where possible
- every chunk carries metadata (`page`, `chapter`, `section`, `chunk_id`, `source_file`)
- `T5.2.TEST` completed with chunk-boundary regression tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S5.2 | T5.2.1 | Add LlamaIndex dependency and configuration controls | Dependency + settings update | 3 |
| S5.2 | T5.2.2 | Implement semantic chunker adapter with structure hints | Semantic chunker module | 6 |
| S5.2 | T5.2.3 | Implement list-preservation policy for numbered/bullet blocks | List-aware chunk policy | 4 |
| S5.2 | T5.2.4 | Attach metadata to chunk models and serialization path | Chunk metadata integration | 4 |
| S5.2 | T5.2.5 | Add fallback to existing section/sentence chunkers | Fallback chunking path | 3 |
| S5.2 | T5.2.TEST | Chunking tests for semantic and fallback modes | Chunking test evidence | 2 |
|  |  | **Epic subtotal** |  | **22** |

### Epic E5.3: PDF-First Ingestion Pipeline from `/data` (18h)

Technical description:
- ingest medical PDFs from `/data/dataset`
- transform parsed pages into semantic chunks
- store chunks and metadata in Qdrant payloads

Primary files:
- `ingestion/ingest_vectordb.py`
- `knowledge/qdrant/ingest.py`
- `rag/chunking/load_documents.py`
- `tests/test_qdrant_ingest.py`

Deliverables:
- PDF ingestion runner
- idempotent upsert logic with metadata-aware point IDs
- ingestion validation report

Dependencies:
- E5.2

Acceptance criteria:
- ingestion pipeline loads PDF corpus from `/data/dataset`
- upserted payload includes page/section/chapter/chunk identifiers
- repeated ingestion does not duplicate existing chunks
- `T5.3.TEST` completed with ingestion integration tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S5.3 | T5.3.1 | Extend loaders to enumerate and parse PDFs from `/data/dataset` | PDF loader integration | 4 |
| S5.3 | T5.3.2 | Update Qdrant ingest payload schema for structured metadata | Metadata-rich Qdrant payloads | 4 |
| S5.3 | T5.3.3 | Update point-id dedup logic to include source/page/chunk identity | Stable dedup id strategy | 4 |
| S5.3 | T5.3.4 | Add ingestion CLI/runtime switches for PDF-first mode | CLI/config integration | 2 |
| S5.3 | T5.3.TEST | PDF ingestion tests with idempotency checks | Ingestion test evidence | 4 |
|  |  | **Epic subtotal** |  | **18** |

### Epic E5.4: Medical NER Pipeline and Entity Normalization (20h)

Technical description:
- extract domain entities (disease, symptom, drug, anatomical structure) from chunks
- compute confidence scores
- normalize aliases and variants to canonical entities

Primary files:
- `agent/reasoning/*` (or new `knowledge/entities/*`)
- `models/contracts.py`
- `config/settings.py`
- `tests/*`

Deliverables:
- NER extraction module with typed output
- entity normalization dictionary/rules
- confidence threshold controls

Dependencies:
- E5.3

Acceptance criteria:
- entity extraction emits type, mention text, canonical form, confidence, and source chunk metadata
- configurable confidence threshold can filter weak entities
- normalization merges duplicates (`MI` vs `myocardial infarction`, etc.)
- `T5.4.TEST` completed with extraction and normalization tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S5.4 | T5.4.1 | Select NER approach and implement extraction pipeline interface | NER pipeline contract | 3 |
| S5.4 | T5.4.2 | Implement medical entity extraction and typed outputs | Entity extraction module | 6 |
| S5.4 | T5.4.3 | Add confidence scoring and threshold-based filtering | Confidence filtering layer | 3 |
| S5.4 | T5.4.4 | Implement canonical normalization and duplicate merging | Normalization module | 4 |
| S5.4 | T5.4.5 | Persist entity annotations linked to `chunk_id` and page | Entity annotation storage | 2 |
| S5.4 | T5.4.TEST | NER + normalization tests | NER test evidence | 2 |
|  |  | **Epic subtotal** |  | **20** |

### Epic E5.5: Relation Extraction and Kuzu Graph Storage (26h)

Technical description:
- extract medical relations from chunk/entity context
- persist entities and edges in KuzuDB
- maintain graph schema and graph ingestion jobs

Primary files:
- `knowledge/graph/*` (new)
- `models/contracts.py`
- `config/settings.py`
- `requirements.txt`

Deliverables:
- graph schema migration scripts
- relation extractor for required predicates
- Kuzu ingestion pipeline and upsert logic

Dependencies:
- E5.4

Acceptance criteria:
- graph supports node types and relations:
- `disease -> symptom`
- `drug -> treats -> disease`
- `condition -> causes -> symptom`
- `disease -> differs_from -> disease`
- relation records include provenance (`source_file`, `page`, `chunk_id`, confidence)
- graph ingestion is idempotent and tested
- `T5.5.TEST` completed with graph integration tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S5.5 | T5.5.1 | Add KuzuDB dependency and implement graph client abstraction | Graph client module | 4 |
| S5.5 | T5.5.2 | Design graph schema for entities, relations, and provenance fields | Graph schema definition | 4 |
| S5.5 | T5.5.3 | Implement relation extraction for required medical predicates | Relation extraction module | 6 |
| S5.5 | T5.5.4 | Build graph ingestion/upsert pipeline from chunked text and NER output | Graph ingestion job | 6 |
| S5.5 | T5.5.5 | Add reconciliation for repeated entities/relations across chunks | Graph dedup logic | 4 |
| S5.5 | T5.5.TEST | Graph schema and ingestion tests | Graph test evidence | 2 |
|  |  | **Epic subtotal** |  | **26** |

### Epic E5.6: Graph-RAG, Citation Guarantees, and Visualization (32h)

Technical description:
- combine vector retrieval (Qdrant) with graph traversal (Kuzu)
- produce citation-rich responses with page/section/chunk traceability
- provide graph visualization with GitNexus and source-chunk/page navigation

Primary files:
- `rag/retrieval/retriever.py`
- `agent/orchestrator/orchestrator.py`
- `api/*`
- `docker-compose.yml`
- `README.md`

Deliverables:
- Graph-RAG retriever/orchestrator strategy
- response citation formatter
- GitNexus integration endpoints/config

Dependencies:
- E5.3, E5.5

Acceptance criteria:
- retrieval can run in vector-only or graph-hybrid mode
- responses include citations with `source_file`, `page`, `section`, `chunk_id`
- GitNexus view can explore nodes/relations and open referenced chunk/page
- `T5.6.TEST` completed with Graph-RAG and citation tests

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S5.6 | T5.6.1 | Implement Graph-RAG retriever that merges vector and graph candidates | Hybrid retriever module | 8 |
| S5.6 | T5.6.2 | Add orchestration policy for graph traversal depth and merge/rerank | Retrieval policy controls | 5 |
| S5.6 | T5.6.3 | Enforce citation output schema in generated answers | Citation formatter + contracts | 4 |
| S5.6 | T5.6.4 | Integrate GitNexus for graph navigation and source linking | Graph visualization integration | 8 |
| S5.6 | T5.6.5 | Add API/CLI controls for Graph-RAG and visualization hooks | Runtime integration controls | 3 |
| S5.6 | T5.6.6 | Update docs/runbooks for graph setup and troubleshooting | Documentation updates | 2 |
| S5.6 | T5.6.TEST | Integration tests for Graph-RAG, citations, and visualization APIs | Graph-RAG test evidence | 2 |
|  |  | **Epic subtotal** |  | **32** |

## Phase P6: Retrieval Quality Hardening (26h)

Goal: improve real-world retrieval quality by removing fragmentary chunks, enforcing embedding readiness, and tightening ranking controls.

### Epic E6.1: Chunk and Retrieval Quality Stabilization (26h)

Technical description:
- enforce high-quality semantic chunking defaults and reject fragmentary chunks
- ensure embeddings backend is real-model based for production-like runs
- add rerank and quality-gate controls to reduce low-value retrieval hits

Primary files:
- `config/settings.py`
- `rag/chunking/strategies.py`
- `rag/chunking/load_documents.py`
- `knowledge/qdrant/ingest.py`
- `rag/retrieval/retriever.py`
- `agent/orchestrator/orchestrator.py`
- `tests/*`

Deliverables:
- chunk quality policy (`min chars/words`, list-aware exceptions)
- startup/runtime guardrails for embeddings and semantic chunking dependencies
- retrieval rerank and threshold hardening
- ingestion quality report artifact

Dependencies:
- E5.6

Acceptance criteria:
- ingestion rejects or merges low-information chunks (for example isolated tokens)
- runtime fails fast (or explicit override required) when fallback embeddings are active
- semantic chunking mode has explicit behavior when LlamaIndex is unavailable
- retrieval output quality improves on tracked probe queries (fewer low-information hits)
- `T6.1.TEST` completed with regression tests and before/after quality metrics

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S6.1 | T6.1.1 | Add startup guard for embedding backend readiness and semantic dependency checks | Startup validation and override controls | 4 |
| S6.1 | T6.1.2 | Rework semantic rechunking to operate on larger structural groups (not only micro-fragments) | Improved semantic chunking pipeline | 5 |
| S6.1 | T6.1.3 | Add chunk quality filters (`min chars/words`) with list-aware exceptions | Chunk quality gate in ingestion | 4 |
| S6.2 | T6.1.4 | Add retrieval rerank pass and stronger low-confidence filtering policy | Retrieval ranking hardening | 5 |
| S6.2 | T6.1.5 | Add ingestion/retrieval quality report (short-chunk ratio, sample hit diagnostics) | Quality report command/output | 4 |
| S6.2 | T6.1.TEST | Add and run regression tests for chunk quality and retrieval relevance | Test and benchmark evidence | 4 |
|  |  | **Epic subtotal** |  | **26** |

## Phase P7: Query Recall and Lexical Fallback (22h)

Goal: close remaining retrieval gaps from `docs/raw_idea/rag_improvements.txt`, especially weak recall cases where relevant PDF content exists but vector-only retrieval misses it.

### Epic E7.1: Keyword Fallback and Chunk Debug Tooling (22h)

Technical description:
- improve PDF normalization for two-column and fragmented bullet text before chunking
- enforce column-aware reading order reconstruction (left column before right column, per page)
- add deterministic keyword fallback retrieval when vector/hybrid confidence is weak
- add operator debug commands for chunk statistics and keyword chunk lookup

Primary files:
- `rag/chunking/load_documents.py`
- `rag/chunking/strategies.py`
- `rag/retrieval/retriever.py`
- `agent/orchestrator/orchestrator.py`
- `rag/retrieval/quality_report.py`
- `run.py`
- `tests/*`

Deliverables:
- stronger line-merge policy for two-column/bullet-heavy PDF pages
- deterministic two-column reflow policy with dehyphenation and line-join rules
- keyword fallback retriever with configurable trigger threshold
- retrieval provenance marker (`vector`, `keyword_fallback`, `hybrid`)
- debug utility command for chunk stats and keyword lookup
- before/after probe report including `Sindromul Cushing`

Dependencies:
- E6.1

Acceptance criteria:
- when vector confidence is below threshold, keyword fallback is attempted automatically
- fallback retrieval returns at least one relevant chunk for tracked weak-recall probes where corpus evidence exists
- two-column pages no longer interleave adjacent left/right column lines in produced chunk text
- debug utility prints chunk count, average length, short-chunk ratio, and top keyword matches
- provenance of final context is visible in logs/debug output
- `T7.1.TEST` completed with regression tests and probe evidence

| Story ID | Task ID | Task | Output Artifact | Estimate (h) |
| --- | --- | --- | --- | --- |
| S7.1 | T7.1.1 | Build weak-recall probe set and baseline retrieval report from current corpus | Baseline probe report | 2 |
| S7.1 | T7.1.2 | Improve two-column reconstruction and bullet line-stitch normalization before semantic chunking | Updated PDF normalization flow | 5 |
| S7.1 | T7.1.3 | Implement keyword fallback retrieval path with confidence trigger policy | Keyword fallback retriever | 5 |
| S7.2 | T7.1.4 | Add fallback merge/ranking and retrieval provenance labeling | Provenance-aware retrieval result | 3 |
| S7.2 | T7.1.5 | Extend debug utility with keyword chunk search and chunk-stat output modes | CLI/debug reporting updates | 3 |
| S7.2 | T7.1.TEST | Add regression tests and before/after probe validation for fallback recall | Test and probe evidence | 4 |
|  |  | **Epic subtotal** |  | **22** |

## Recommended Execution Order

1. P0 (planning/governance baseline)
2. P1 (structure, CLI, typed models)
3. P2 (orchestration and safety behavior)
4. P3 (quality and observability)
5. P4 (containers, API, release documentation)
6. P5 (semantic chunking, knowledge graph, Graph-RAG, visualization)
7. P6 (retrieval quality hardening and operational quality gates)
8. P7 (query recall hardening via lexical fallback and debug tooling)

Priority constraints:
- complete E1.4 before major P2 work
- complete E2.1 before E2.2 and E2.3
- complete E4.4 before final release checklist in E4.3
- complete E5.1 before E5.2 and E5.3
- complete E5.4 before E5.5
- complete E5.5 before E5.6 Graph-RAG rollout
- complete E5.6 before E6.1 retrieval hardening rollout
- complete E6.1 before E7.1 lexical fallback rollout

## Handover Checklist for New Developers

- Read `docs/prd.md`, then `docs/backlog.md`, then `docs/backlog-tracker.md`.
- Pick first `TODO` task in active phase and mark `IN_PROGRESS`.
- Before coding, note expected output artifact from task row.
- After coding, update tracker with actual hours, changed files, and validation command output summary.
- Do not close epic without `*.TEST` task marked `DONE`.
