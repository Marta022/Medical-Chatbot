# Medical Chatbot PRD

Date: 2026-02-13  
Version: 1.1  
Status: In Implementation (Phase 4 active)  
Primary reference backlog: `docs/backlog.md`  
Tracking document: `docs/backlog-tracker.md`

## 1. Problem Statement

The project needs a medically oriented chatbot that uses retrieval-augmented generation (RAG), safety guardrails, and LLM reasoning to answer health-related questions in Romanian while avoiding unsafe guidance. The current codebase contains partial building blocks, but core product behavior is not yet implemented end-to-end.

## 2. Goals

1. Provide grounded medical information using retrieved context, not hallucinated facts.
2. Detect emergency or unsafe intent and return safe escalation guidance instead of advice.
3. Implement a deterministic orchestration flow with evaluation and retry/fallback logic.
4. Offer reproducible local and containerized execution.
5. Expose REST endpoints compatible with OpenWebUI integration.

## 3. Non-Goals

1. Replacing licensed medical professionals or issuing definitive diagnoses.
2. Realtime emergency dispatch or direct integration with hospital systems.
3. Training custom foundation models in this phase.
4. Supporting every language beyond Romanian and operational English prompts.

## 4. Target Users and Stakeholders

| Role | Needs | Success Signal |
| --- | --- | --- |
| End user (patient/curious user) | Reliable informational answers and safe handling of urgent intent | Receives clear, grounded, non-harmful response |
| Thesis developer | Modular architecture, clear backlog, measurable progress | Can execute tasks independently and verify results |
| Advisor/reviewer | Traceable engineering process and validation evidence | Can map implementation to requirements and results |

## 5. Scope

### In Scope

1. CLI-based runtime for chat, ingestion, and evaluation flows.
2. RAG retrieval over medical datasets via Qdrant.
3. Rule-based and optional LLM-based guardrails.
4. Evaluator loop with retry/fallback behavior.
5. REST API including OpenAI-compatible endpoints for OpenWebUI.
6. Containerized deployment with `app`, `qdrant`, and `openwebui` services.

### Out of Scope

1. Production-grade identity/access platform.
2. Certified medical device workflow compliance.
3. Fine-tuning and serving custom transformer models.

## 5.1 Implementation Snapshot (2026-02-25)

Implemented:
- Unified CLI entrypoint (`run.py`) with `chat`, `ingest`, `eval`
- Orchestrator with guardrails, retrieval, evaluator retry guidance, and provider fallback
- Typed contracts across runtime (`models/*`)
- Containerization and compose topology (`Dockerfile`, `docker-compose.yml`, optional `local-llm` profile)
In progress:
- Operations/release documentation finalization (`E4.3`)
Not implemented yet:
- REST/OpenAI-compatible API layer (`E4.4`) in `api/*`

## 6. User Journeys

### Journey A: Informational Medical Query

1. User asks symptom/disease informational question.
2. Guardrails classify as safe informational.
3. System retrieves relevant context from vector DB.
4. LLM generates structured Romanian answer from context.
5. Evaluator validates grounding/safety/language.
6. Response returned.

### Journey B: Emergency Signal

1. User input contains emergency indicators.
2. Guardrails classify as emergency.
3. RAG and generation are bypassed.
4. User receives urgent escalation message (for example emergency number and immediate care guidance).

### Journey C: OpenWebUI Client Request

1. OpenWebUI sends request to OpenAI-compatible endpoint.
2. API maps payload to internal typed request model.
3. Orchestrator executes full pipeline.
4. API returns OpenAI-compatible response format.

## 7. Functional Requirements

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-01 | System must apply guardrails before retrieval/generation. | Must |
| FR-02 | System must detect emergency/unsafe intent and block unsafe advice. | Must |
| FR-03 | System must perform RAG retrieval for safe informational queries. | Must |
| FR-04 | System must generate responses in Romanian for user-facing output. | Must |
| FR-05 | System must evaluate generated response quality and safety. | Must |
| FR-06 | System must retry with adjusted prompt and/or fallback provider when evaluation fails. | Must |
| FR-07 | System must expose CLI commands for chat, ingest, and eval. | Must |
| FR-08 | System must store/retrieve vectors via Qdrant with collection lifecycle management. | Must |
| FR-09 | System must expose REST endpoints for engine functions. | Must |
| FR-10 | System must expose OpenAI-compatible chat endpoints for OpenWebUI compatibility. | Must |
| FR-11 | Core runtime payloads must be represented by Python models, not ad-hoc dicts. | Must |
| FR-12 | Progress and execution evidence must be tracked per task in tracker file. | Must |

## 8. Non-Functional Requirements

| ID | Requirement | Target |
| --- | --- | --- |
| NFR-01 | Safety routing precision for emergency/unsafe benchmark set | >=95% correct route classification |
| NFR-02 | Grounded response behavior on benchmark with known context | >=90% responses cite/reflect retrieved context |
| NFR-03 | Romanian language compliance for user-visible responses | >=98% benchmark responses in Romanian |
| NFR-04 | End-to-end p95 latency (chat path, excluding cold start) | <=7s local dev baseline |
| NFR-05 | Service startup reliability (compose stack) | >=95% successful startup in smoke runs |
| NFR-06 | Code maintainability | PEP8/lint checks pass on first-party modules |
| NFR-07 | Test discipline | Every epic has completed `*.TEST` task |

## 9. Architecture Context and Ownership

| Component | Responsibility | Owner |
| --- | --- | --- |
| `agent/orchestrator` | Main workflow and retry policy | Thesis developer |
| `agent/guardrail` | Safety classification and escalation messages | Thesis developer |
| `agent/evaluation` | Output validation and scoring | Thesis developer |
| `rag/retrieval` | Context lookup and ranking | Thesis developer |
| `rag/chunking` | Chunk strategy for ingestion | Thesis developer |
| `knowledge/qdrant` | Vector DB lifecycle and operations | Thesis developer |
| `models` | Typed contracts for core objects | Thesis developer |
| `api` | REST and OpenAI-compatible interface (planned in E4.4) | Thesis developer |
| `config` | Prompt/env/logging configuration | Thesis developer |

## 10. Requirement Traceability Matrix

| Requirement ID | Backlog Tasks | Components |
| --- | --- | --- |
| FR-01 | `T2.1.1`, `T2.2.1` | `agent/orchestrator`, `agent/guardrail` |
| FR-02 | `T2.2.2`, `T2.2.4`, `T2.2.TEST` | `agent/guardrail` |
| FR-03 | `T2.3.2`, `T2.3.4`, `T2.3.TEST` | `rag/retrieval`, `rag/chunking` |
| FR-04 | `T2.1.4`, `T2.1.TEST` | `agent/orchestrator`, `agent/evaluation` |
| FR-05 | `T2.1.4`, `T2.1.6`, `T2.1.TEST` | `agent/evaluation` |
| FR-06 | `T2.1.3`, `T2.1.TEST` | `agent/orchestrator`, `llm_hub/router` |
| FR-07 | `T1.2.1`, `T1.2.2`, `T1.2.TEST` | CLI entrypoint |
| FR-08 | `T2.3.1`, `T2.3.6`, `T2.3.TEST` | `knowledge/qdrant`, ingestion |
| FR-09 | `T4.4.1`, `T4.4.2`, `T4.4.TEST` | `api` |
| FR-10 | `T4.4.3`, `T4.4.5`, `T4.4.TEST` | `api`, OpenWebUI integration |
| FR-11 | `T1.4.2`, `T1.4.3`, `T1.4.TEST` | `models`, runtime modules |
| FR-12 | `T0.2.1`, `T0.2.2`, `T0.2.TEST` | `docs/backlog-tracker.md` |
| NFR-01 | `T2.2.TEST`, `T3.3.1` | guardrail + tests |
| NFR-02 | `T2.1.TEST`, `T3.3.2` | orchestrator + tests |
| NFR-03 | `T2.1.4`, `T3.3.TEST` | evaluator + tests |
| NFR-04 | `T3.1.1`, `T3.3.TEST` | observability + tests |
| NFR-05 | `T4.2.TEST`, `T4.1.TEST` | container stack |
| NFR-06 | `T3.2.1`, `T3.2.TEST` | style/lint gate |
| NFR-07 | all `*.TEST` tasks | all epics |

## 11. Rollout Plan

1. Phase 0: finalize PRD and governance baseline.
2. Phase 1: restructure architecture, introduce CLI, and typed models.
3. Phase 2: implement full orchestrator, guardrails, and robust RAG flow.
4. Phase 3: complete observability, style gates, and automated testing.
5. Phase 4: deliver containers, REST API, OpenWebUI integration, and release docs.

## 12. Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| External model/provider/network instability | Delayed tests and uncertain runtime behavior | Mock provider tests + fallback providers + explicit degraded mode |
| Missing module implementations in current codebase | Integration blockers | Prioritize typed-model and orchestrator foundations first |
| Safety false negatives in guardrails | High | Expand test corpus and enforce safety test gates per epic |
| Documentation drift from implementation | Medium | Update tracker and docs on every step with evidence |

## 13. Advisor Review Checklist (T0.1.5)

- [x] Problem and scope align with thesis topic.
- [x] In-scope and out-of-scope boundaries are explicit.
- [x] Functional requirements are mapped to backlog and components.
- [x] Non-functional metrics are measurable.
- [x] Risks and mitigations are documented.
- [x] Rollout path is phase-aligned with backlog.

## 14. PRD Validation Checklist (T0.1.TEST)

- [x] `docs/prd.md` created and versioned.
- [x] Contains goals, non-goals, constraints, architecture context, risks, rollout.
- [x] Requirements linked to backlog task IDs.
- [x] Requirement matrix references existing component targets.
- [x] Cross-reference paths exist: `docs/backlog.md`, `docs/backlog-tracker.md`.

## 15. Change Log

| Date | Version | Change |
| --- | --- | --- |
| 2026-02-13 | 1.0 | Initial PRD baseline authored from raw idea docs and backlog scope |
| 2026-02-25 | 1.1 | Aligned PRD to implementation state (CLI/orchestrator/containers complete; API marked as planned in E4.4) and synchronized ownership/architecture references |

