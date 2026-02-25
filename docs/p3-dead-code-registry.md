# Dead Code Registry (P3)

Last updated: 2026-02-25

Scope: empty or placeholder modules, shims pending removal, and packages with no functional code.

## Empty Modules

- `api/__init__.py`
  - Status: empty package marker
  - Reason: reserved for API scaffold in E4.4
  - Action: keep until E4.4 implementation

- `tests/__init__.py`
  - Status: empty package marker
  - Reason: enables tests package import
  - Action: keep

## Placeholder / Shim Modules

All of the following contain `# TODO(remove-shim): remove after P2 stabilization.` and are shim adapters to keep legacy imports working during reorg:

- `agents/main_agent.py` -> delegates to `run.py`
- `evaluation/benchmark.py` -> shim to `agent/evaluation/benchmark.py`
- `evaluation/evaluator.py` -> shim to `agent/evaluation/evaluator.py`
- `guardrails/llm_guardrail.py` -> shim to `agent/guardrail/llm_guardrail.py`
- `guardrails/rules.py` -> shim to `agent/guardrail/rules_engine.py`
- `ingestion/embed.py` -> shim to `knowledge/qdrant/embed.py`
- `ingestion/ingest_vectordb.py` -> shim to `knowledge/qdrant/ingest.py`
- `ingestion/load_documents.py` -> shim to `rag/chunking/load_documents.py`
- `llm_hub/anthropic_client.py` -> shim to `agent/reasoning/clients/anthropic_client.py`
- `llm_hub/local_gemma_client.py` -> shim to `agent/reasoning/clients/local_gemma_client.py`
- `llm_hub/openai_client.py` -> shim to `agent/reasoning/clients/openai_client.py`
- `llm_hub/router.py` -> shim to `agent/reasoning/llm_router.py`
- `rag/retriever.py` -> shim to `rag/retrieval/retriever.py`
- `translation/translator.py` -> shim to `agent/reasoning/translator.py`
- `vector_db/qdrant_client.py` -> shim to `knowledge/qdrant/client.py`

Action: remove once Phase 2 stabilization is complete and legacy import paths are no longer required.
