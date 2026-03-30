# Phase 1 Compatibility Shim Register (T1.1.3)

Date: 2026-02-13  
Task ID: `T1.1.3`

## Purpose

Track temporary legacy-path compatibility modules introduced during migration so they can be removed predictably after stabilization.

## Shim Scope

All shim files must include:
- `TODO(remove-shim)` comment
- direct re-export or thin wrapper only (no new business logic)
- removal target: end of Phase 2 stabilization

## Shim Inventory

| Legacy Path | New Canonical Module | Shim Type | Removal Target |
| --- | --- | --- | --- |
| `agents/main_agent.py` | `agent/orchestrator/chat_loop.py` | Delegating entrypoint | End of P2 |
| `guardrails/rules.py` | `agent/guardrail/rules_engine.py` | Wrapper + dict compatibility | End of P2 |
| `guardrails/llm_guardrail.py` | `agent/guardrail/llm_classifier.py` | Re-export | End of P2 |
| `rag/retriever.py` | `rag/retrieval/retriever.py` | Wrapper returning legacy tuple format | End of P2 |
| `ingestion/embed.py` | `rag/retrieval/embeddings.py` | Re-export | End of P2 |
| `ingestion/load_documents.py` | `rag/chunking/load_documents.py` | Re-export | End of P2 |
| `ingestion/ingest_vectordb.py` | `knowledge/qdrant/ingest.py` | Delegating script entrypoint | End of P2 |
| `vector_db/qdrant_client.py` | `knowledge/qdrant/client.py` | Re-export | End of P2 |
| `llm_hub/router.py` | `agent/reasoning/llm_router.py` | Re-export | End of P2 |
| `llm_hub/openai_client.py` | `agent/reasoning/providers/openai_client.py` | Re-export | End of P2 |
| `llm_hub/local_gemma_client.py` | `agent/reasoning/providers/local_gemma_client.py` | Re-export | End of P2 |
| `llm_hub/anthropic_client.py` | `agent/reasoning/providers/anthropic_client.py` | Re-export | End of P2 |
| `translation/translator.py` | `agent/reasoning/translator.py` | Re-export | End of P2 |
| `evaluation/evaluator.py` | `agent/evaluation/evaluator.py` | Re-export | End of P2 |
| `evaluation/benchmark.py` | `agent/evaluation/benchmark.py` | Re-export | End of P2 |

## Removal Plan

1. Phase 2: stop adding new imports against legacy paths.
2. Phase 2: run stale-import scan and replace legacy imports with canonical imports.
3. End of Phase 2: remove shim files in one cleanup commit.
4. Phase 3 tests must run with no shim dependencies.

