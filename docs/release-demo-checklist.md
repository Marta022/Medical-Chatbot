# Release and Demo Checklist

Date: 2026-02-25  
Task ID: `T4.3.3`

## 1. Release Readiness Checklist

- [ ] Repository state is clean enough for release handoff (document any intentional local diffs).
- [ ] `.env` is configured from `.env.example` with valid provider and Qdrant settings.
- [ ] Required datasets exist at:
- `data/dataset/disease_database.json`
- `data/dataset/dataset_sheet1.csv`
- [ ] Qdrant collection is available and ingest path succeeds (`python main.py ingest`).
- [ ] CLI commands are verified:
- `python main.py --help`
- `python main.py eval`
- [ ] Guardrail behavior is verified with at least one emergency and one unsafe prompt.
- [ ] Retrieval behavior is verified with at least one known in-domain medical query.
- [ ] Evaluator retry/fallback path is validated through test evidence in tracker logs.
- [ ] Test suite and coverage threshold pass:
- `python -m coverage run -m unittest`
- `python -m coverage report --fail-under=80`
- [ ] Docker image smoke checks pass:
- `docker build --no-cache -t medical-chatbot:test .`
- `docker run --rm medical-chatbot:test python main.py --help`
- [ ] Compose topology checks pass:
- `docker compose up -d`
- `docker compose ps`
- `docker compose down`

## 2. Demo Checklist

- [ ] Start stack for demo context:
- `docker compose up -d qdrant app`
- [ ] Show CLI help and supported modes.
- [ ] Run a safe informational prompt and show grounded response.
- [ ] Run an emergency prompt and show guardrail escalation behavior.
- [ ] Show retrieval context logging from chat flow.
- [ ] Run `python main.py eval` and show evaluator output structure.
- [ ] If presenting OpenWebUI, start it and show service reachability (`http://localhost:3000`).
- [ ] Stop demo services cleanly (`docker compose down`).

## 3. Risk Register

| ID | Risk | Impact | Likelihood | Mitigation | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| R-01 | External provider/API instability | High | Medium | Keep provider fallback order enabled; maintain mocked tests and offline-safe validation path | Thesis developer | Open |
| R-02 | Guardrail false negatives on unseen phrasing | High | Medium | Expand emergency/unsafe phrase corpus and regression tests each release | Thesis developer | Open |
| R-03 | Retrieval quality degradation due to ingestion/data drift | Medium | Medium | Re-run ingest validation and retrieval smoke checks before demo/release | Thesis developer | Open |
| R-04 | Docker/engine instability on local machine | Medium | Medium | Keep no-cache build fallback; capture daemon health and restart/cleanup procedure in tracker | Thesis developer | Monitoring |
| R-05 | Documentation drift from implementation | Medium | Medium | Update `docs/backlog-tracker.md` after each task and re-check PRD/architecture at milestone boundaries | Thesis developer | Open |
| R-06 | Pending API/OpenWebUI compatibility work not fully complete | Medium | High | Track as `E4.4` gated deliverable before final release sign-off | Thesis developer | Open |

