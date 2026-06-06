# P6 Retrieval Quality Report

Date: 2026-03-05
Task scope: `T6.1.TEST`

## Benchmark Dataset

- `data/dataset/DORIN-CURS_SEM2_searchable.pdf`

## Chunk Quality Benchmark

Command used:

```powershell
python - <<'PY'
from rag.chunking.load_documents import load_pdf_chunks
from statistics import mean
pdf='data/dataset/DORIN-CURS_SEM2_searchable.pdf'
for strategy in ['section','semantic']:
    chunks=load_pdf_chunks(pdf, chunking_strategy=strategy, semantic_chunk_max_chars=700, semantic_use_llamaindex=False)
    lens=[len(c.text.strip()) for c in chunks if c.text and c.text.strip()]
    short20=sum(1 for n in lens if n<20)
    short40=sum(1 for n in lens if n<40)
    print('| {} | {} | {} | {} | {} |'.format(strategy,len(lens),round(mean(lens),2),round(short20/len(lens),4),round(short40/len(lens),4)))
PY
```

Observed results:

| Strategy | Chunk count | Avg chars | Ratio `<20` | Ratio `<40` |
| --- | --- | --- | --- | --- |
| section | 7619 | 218.76 | 0.1484 | 0.2561 |
| semantic | 1825 | 916.47 | 0.0044 | 0.0323 |

## Regression Suite

Command used:

```powershell
python -m unittest tests.test_pdf_structure tests.test_chunking tests.test_qdrant_ingest tests.test_retriever tests.test_retrieval_filters tests.test_orchestrator tests.test_quality_report tests.test_config_prompts tests.test_cli -v
```

Result:

- `OK` (64 tests)

## Summary

- Semantic grouping + rechunking reduced short-fragment chunks substantially.
- Ingest-time quality gates and retrieval rerank are covered by regression tests.
- Startup guards and diagnostics reporting paths are validated.
