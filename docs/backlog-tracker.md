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
| Completed effort | 12h |
| In-progress effort | 0h |
| Remaining effort | 226h |
| Overall completion | 5% |

## Phase Progress

| Phase | Planned (h) | Done (h) | In Progress (h) | Remaining (h) | Status |
| --- | --- | --- | --- | --- | --- |
| P0 Product Definition and Planning | 28 | 12 | 0 | 16 | IN_PROGRESS |
| P1 Architecture and Codebase Reorganization | 60 | 0 | 0 | 60 | TODO |
| P2 Core Orchestration and Safety Pipeline | 50 | 0 | 0 | 50 | TODO |
| P3 Code Quality and Observability | 40 | 0 | 0 | 40 | TODO |
| P4 Runtime and Delivery | 60 | 0 | 0 | 60 | TODO |

## Epic Progress

| Epic ID | Epic | Planned (h) | Done (h) | Status | Notes |
| --- | --- | --- | --- | --- | --- |
| E0.1 | PRD Authoring and Scope Baseline | 16 | 2 | IN_PROGRESS | `T0.1.1` complete based on raw-idea analysis |
| E0.2 | Backlog Governance and Tracker Setup | 12 | 10 | IN_PROGRESS | Governance/tracker setup tasks completed except risk-buffer task |
| E1.1 | Repository Restructuring to Target Layout | 24 | 0 | TODO | Includes mandatory epic test task |
| E1.2 | Unified CLI Entrypoint | 10 | 0 | TODO | Includes mandatory epic test task |
| E1.3 | Configuration and Prompt Normalization | 10 | 0 | TODO | Includes mandatory epic test task |
| E1.4 | Domain Models and Typed Contracts | 16 | 0 | TODO | New epic for replacing hardcoded dict objects |
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

## Active Task Board

Use this section for current work only (max 10 items at a time).

| Task ID | Task | Estimate (h) | Actual (h) | Owner | Status | Start | End | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| T0.1.1 | Extract requirements from `docs/raw_idea/*` and normalize terminology | 2 | 2 | Codex | DONE | 2026-02-13 | 2026-02-13 | Completed during backlog grounding steps |
| T0.2.1 | Define backlog ID convention and status lifecycle | 2 | 2 | Codex | DONE | 2026-02-13 | 2026-02-13 | Defined in backlog/tracker governance sections |
| T0.2.2 | Define tracker metrics (planned, actual, blocked, carryover) | 2 | 2 | Codex | DONE | 2026-02-13 | 2026-02-13 | Implemented in tracker global/phase/epic tables |
| T0.2.3 | Define update cadence and DoR/DoD gates | 2 | 2 | Codex | DONE | 2026-02-13 | 2026-02-13 | Captured in mandatory execution rules and DoD |
| T0.2.5 | Define changelog procedure for every step | 2 | 2 | Codex | DONE | 2026-02-13 | 2026-02-13 | Work log procedure active and used |
| T0.2.TEST | Dry-run tracker lifecycle on sample task | 2 | 2 | Codex | DONE | 2026-02-13 | 2026-02-13 | Multiple planning updates logged as lifecycle evidence |
| T0.1.2 | Draft PRD core sections | 4 | 0 | TBD | TODO |  |  | Waiting for `docs/prd.md` creation |
| T0.2.4 | Calibrate estimates and risk buffer model | 2 | 0 | TBD | TODO |  |  | Estimates calibrated; explicit risk-buffer policy still missing |
| T1.4.1 | Inventory hardcoded objects currently passed as dicts | 2 | 0 | TBD | TODO |  |  | Supports typed model migration |
| T4.4.1 | Create API application skeleton and dependency wiring | 4 | 0 | TBD | TODO |  |  | Enables OpenWebUI integration |

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

## Known Risks and Blockers

- Current environment restrictions prevent downloading external model artifacts during runtime checks.
- Several modules are placeholders/empty and will require first implementation before integration tests can pass.
- Existing import mismatch around Qdrant collection setup can block ingestion until fixed.
