# Phase 1 Migration Plan (T1.1.1)

Date: 2026-02-13  
Task ID: `T1.1.1`  
Phase: `P1`  
Epic: `E1.1`  
Owner: TBD

## 1. Objective

Define a concrete, low-risk migration plan from the current repository layout to the target layout agreed in `docs/backlog.md`, so implementation task `T1.1.2` can execute without additional discovery.

## 2. Scope

In scope for this planning task:
- target package tree
- file-by-file migration mapping
- execution waves and order of operations
- import compatibility strategy
- validation and rollback checklist

Out of scope for this planning task:
- physically moving code files
- refactoring business logic behavior
- changing runtime provider implementations

## 3. Current First-Party Module Inventory

- `agents/*`
- `config/*`
- `evaluation/*`
- `guardrails/*`
- `ingestion/*`
- `llm_hub/*`
- `rag/*`
- `translation/*`
- `vector_db/*`
- `data/*`

## 4. Target Package Tree

```text
code/
  config/
  agent/
    __init__.py
    orchestrator/
      __init__.py
    guardrail/
      __init__.py
    evaluation/
      __init__.py
    reasoning/
      __init__.py
  data/
    dataset/
  knowledge/
    __init__.py
    qdrant/
      __init__.py
  rag/
    __init__.py
    chunking/
      __init__.py
    retrieval/
      __init__.py
  models/
    __init__.py
  api/
    __init__.py
```

Notes:
- `models/` and `api/` are included because they are required by already-approved backlog scope (`E1.4`, `E4.4`).
- Existing top-level runtime files (`app.py`) remain temporarily until `E1.2` CLI migration is complete.

## 5. File Migration Map (Old -> New)

| Old Path | New Path | Why |
| --- | --- | --- |
| `agents/main_agent.py` | `agent/orchestrator/chat_loop.py` | Main runtime orchestration entry |
| `guardrails/rules.py` | `agent/guardrail/rules_engine.py` | Rule-based safety logic |
| `guardrails/llm_guardrail.py` | `agent/guardrail/llm_classifier.py` | LLM-assisted safety classification |
| `evaluation/evaluator.py` | `agent/evaluation/evaluator.py` | Response quality/safety evaluation |
| `evaluation/benchmark.py` | `agent/evaluation/benchmark.py` | Evaluation benchmark tooling |
| `translation/translator.py` | `agent/reasoning/translator.py` | Language conversion helper |
| `llm_hub/router.py` | `agent/reasoning/llm_router.py` | Provider routing |
| `llm_hub/openai_client.py` | `agent/reasoning/providers/openai_client.py` | Provider client |
| `llm_hub/local_gemma_client.py` | `agent/reasoning/providers/local_gemma_client.py` | Provider client |
| `llm_hub/anthropic_client.py` | `agent/reasoning/providers/anthropic_client.py` | Provider client |
| `rag/retriever.py` | `rag/retrieval/retriever.py` | Retrieval-only responsibility |
| `ingestion/embed.py` | `rag/retrieval/embeddings.py` | Shared embedding operations |
| `ingestion/load_documents.py` | `rag/chunking/load_documents.py` | Source parsing/chunk preparation |
| `ingestion/ingest_vectordb.py` | `knowledge/qdrant/ingest.py` | Qdrant ingestion workflow |
| `vector_db/qdrant_client.py` | `knowledge/qdrant/client.py` | Qdrant lifecycle and client |
| `data/disease_database.json` | `data/dataset/disease_database.json` | Dataset consolidation |
| `data/dataset - Sheet1.csv` | `data/dataset/dataset_sheet1.csv` | Dataset consolidation + normalized filename |

## 6. Execution Waves

### Wave 1: Skeleton and Package Scaffolding

1. Create target directories and `__init__.py` files.
2. Add placeholder package docs/comments where needed.

### Wave 2: Low-Risk Moves

1. Move evaluation and guardrail modules.
2. Update direct imports in dependent modules.

### Wave 3: RAG + Knowledge

1. Move retrieval/chunking modules and qdrant client.
2. Move ingestion workflows.
3. Fix known `ensure_collection` ownership at new `knowledge/qdrant/client.py`.

### Wave 4: Reasoning Layer

1. Move `llm_hub` and translation modules to `agent/reasoning`.
2. Update router/provider import paths.

### Wave 5: Dataset and Path Normalization

1. Move dataset files to `data/dataset`.
2. Update hardcoded file paths.

### Wave 6: Compatibility Shims and Cleanup

1. Add temporary shim modules in old paths re-exporting from new paths.
2. Mark all shims with removal target (end of P2).

## 7. Compatibility Strategy

During migration:
- keep old import paths functional with thin shims to reduce breakage
- add a `TODO(remove-shim)` marker in every shim file
- do not maintain shims longer than Phase 2 completion

Example shim pattern:

```python
# TODO(remove-shim): remove after P2 stabilization.
from agent.guardrail.rules_engine import *  # noqa: F401,F403
```

## 8. Validation Checklist for T1.1.2

After each wave:
1. run path search for stale imports:
   - `rg "from (agents|guardrails|evaluation|ingestion|llm_hub|vector_db|translation|rag\\.retriever)" -n`
2. run import smoke checks on lightweight modules (avoid model-download side effects).
3. run targeted CLI or module entry smoke check when `E1.2` is active.
4. update tracker with changed files and issues.

Definition of migration done for `E1.1`:
- target structure exists and imports resolve
- dataset paths updated
- shims documented and time-bounded
- `T1.1.TEST` completed and logged

## 9. Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Import breakage across moved modules | Runtime failures | Wave-based migration + shim strategy |
| Hidden hardcoded paths | Ingestion failure | `rg` search for old paths before closeout |
| Runtime side effects during import checks (external model download) | Slow or blocked validation | limit smoke checks to non-network modules until provider/mocking gates are ready |
| Mixed old/new package usage drift | Maintenance complexity | enforce stale import scan in validation checklist |

## 10. Rollback Approach

If a wave fails:
1. stop further moves
2. restore affected files in that wave only
3. keep previously stable waves intact
4. document failure root cause in tracker and split a follow-up task if required

## 11. Evidence of Completion for T1.1.1

- This document (`docs/p1-migration-plan.md`) exists.
- It includes target tree, old/new mapping, migration waves, validation strategy, and rollback.
- Tracker work log references this artifact.

