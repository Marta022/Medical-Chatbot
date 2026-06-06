# Dead Code Registry (P3)

Last updated: 2026-03-12

Scope: empty or placeholder modules, shims pending removal, and packages with no functional code.

## Empty Modules

- `tests/__init__.py`
  - Status: empty package marker
  - Reason: enables tests package import
  - Action: keep

## Active Placeholder / Shim Modules

All of the following contain `# TODO(remove-shim): remove after P2 stabilization.` and are shim adapters to keep legacy imports working during reorg:

- `evaluation/benchmark.py` -> shim to `agent/evaluation/benchmark.py`
- `evaluation/evaluator.py` -> shim to `agent/evaluation/evaluator.py`
- `guardrails/rules.py` -> shim to `agent/guardrail/rules_engine.py`
- `ingestion/load_documents.py` -> shim to `rag/chunking/load_documents.py`
- `llm_hub/router.py` -> shim to `agent/reasoning/llm_router.py`
- `vector_db/qdrant_client.py` -> shim to `knowledge/qdrant/client.py`

## Removed in Cleanup (2026-03-12)

- `agents/main_agent.py`
- `guardrails/llm_guardrail.py`
- `ingestion/embed.py`
- `ingestion/ingest_vectordb.py`
- `llm_hub/anthropic_client.py`
- `llm_hub/local_gemma_client.py`
- `llm_hub/openai_client.py`
- `llm_hub/qwen_client.py`
- `rag/retriever.py`
- `translation/translator.py`

Action: remove once Phase 2 stabilization is complete and legacy import paths are no longer required.
