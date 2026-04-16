# Phase 1 Import and Path Validation (T1.1.6)

Date: 2026-02-13  
Task ID: `T1.1.6`

## Goal

Validate that migrated package layout resolves imports correctly and that runtime path assumptions (datasets, prompt file) match current defaults.

## Checks Executed

1. Import smoke for migrated modules:
   - `python -c "import run; import agent.orchestrator.chat_loop; import agent.guardrail.rules_engine; import knowledge.qdrant.client; import rag.retrieval.retriever; import models.contracts; print('import-smoke-ok')"`
2. Compile validation:
   - `python -m compileall agent knowledge rag models config run.py`
3. Stale-import scan for canonical modules:
   - `rg "from (agents|guardrails|evaluation|ingestion|llm_hub|vector_db|translation|rag\\.retriever)" -n agent knowledge rag models run.py`
4. Dataset path checks:
   - `data/dataset/disease_database.json` exists
   - `data/dataset/dataset_sheet1.csv` exists
5. Startup validation checks:
   - `run.py eval` works with current defaults
   - settings validation functions present (`validate_startup`, `ensure_startup_valid`)
6. Phase-1 test suite:
   - `python -m unittest tests.test_models tests.test_cli tests.test_config_prompts tests.test_phase1_structure -v`

## Results

| Check | Result |
| --- | --- |
| Migrated imports | PASS |
| Compile validation | PASS |
| Stale-import scan on canonical modules | PASS (no matches) |
| Dataset normalized paths | PASS |
| CLI eval smoke | PASS |
| Phase-1 unittest suite | PASS (20 tests) |

## Notes

- Stale-import scanning should continue in Phase 2 until all shim consumers are removed.
- External model/download behavior is intentionally not part of this validation record.
