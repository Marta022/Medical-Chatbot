# Hardcoded Object Inventory (T1.4.1)

Date: 2026-02-13  
Task ID: `T1.4.1`

## Goal

Identify implicit dictionary-shaped objects in current runtime flows and map them to explicit Python models.

## Inventory

| Legacy Location | Legacy Shape | Risk | New Model |
| --- | --- | --- | --- |
| `guardrails/rules.py` | `{"is_emergency","is_unsafe","is_valid","message"}` | Missing keys at runtime, no type checks | `models.contracts.GuardrailResult` |
| `rag/retriever.py` | tuple `(results: list[str], titles: list[str])` | Positional unpacking fragility | `models.contracts.RetrievalResult` + `RetrievalHit` |
| `llm_hub/router.py` | inline message dict list | Mixed caller payload formats | `models.contracts.LLMRequest` + `LLMMessage` |
| `ingestion/load_documents.py` | per-item dict with mixed optional fields | Silent schema drift | `models.contracts.MedicalItem` |
| `agents/main_agent.py` | ad-hoc query/top_k variables | Inconsistent request contract | `models.contracts.QueryRequest` |
| evaluator response (planned) | ad-hoc booleans/scores | weak retry criteria consistency | `models.contracts.EvaluatorResult` |

## Migration Decision

All new code in `agent/*`, `rag/retrieval/*`, and `knowledge/*` will consume typed models directly.  
Legacy module paths keep compatibility shims temporarily and may still expose old shapes for backward compatibility.

## Completion Criteria

- [x] Core dict-like runtime objects inventoried.
- [x] One-to-one mapping to typed models documented.
- [x] Used as input for `T1.4.2` implementation.

