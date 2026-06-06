# Benchmark Demo

Standalone demo for the benchmark module:

```bash
python run_benchmark_demo.py
```

The demo runs the first answered grid item from `data/dataset/benchmark_questions.json`
and uses `data/dataset/benchmark_responses.json` as the answer key.

The console logs show only the benchmark architecture:

- grila selectata
- retrieval fan-out pentru intrebare + variante
- cautari Qdrant multiple, pooling si rerank
- top-k context trimis la LLM
- comparatie cu answer key si metrici
- artifact JSON

The JSON artifact is written to:

```text
output/benchmark_demo_first_grid.json
```

Per-request HTTP logs from OpenAI/Qdrant clients are hidden so the demo output stays focused
on the benchmark flow.

Useful options:

```bash
python run_benchmark_demo.py --top-k 3
python run_benchmark_demo.py --output output/my_demo.json
```

This entrypoint is separate from `run.py`, so the main CLI behavior remains unchanged.
