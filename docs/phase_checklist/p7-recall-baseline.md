# P7 Weak-Recall Baseline

Date: 2026-03-05
Scope: `T7.1.1` baseline probe before E7.1 retrieval changes are fully rolled out

## Inputs

- Retrieval mode: `vector`
- Chunking strategy: `section`
- Semantic max chars: `700`
- Semantic LlamaIndex enabled: `True`
- PDF paths: `['data\\dataset\\DORIN-CURS_SEM2_searchable.pdf']`

## Chunk Metrics

- `data\dataset\DORIN-CURS_SEM2_searchable.pdf` -> count=5218, avg_chars=319.87, avg_words=46.53, short_lt_40_ratio=0.1665

## Keyword Chunk Probes

- `data\dataset\DORIN-CURS_SEM2_searchable.pdf`
  - `sindromul cushing`: 4 matches
    - page=2 section=unknown chunk_id=a21c788a44bcbc9a hits=1 preview=Pneumonia interstiţială acută ......................................... 88 Alte cauze de leziuni pulmonare int
    - page=5 section=MAC =MAC; chunk_id=4fee367ea5b03c61 hits=1 preview=RRVS = radiografie renovezicală simplă; MAT= microangiopatie trombotică; RVPu = rezistenţei vasculare pulmonar
    - page=159 section=0 HT A chunk_id=31c7db8e0ab79c75 hits=1 preview=cardiovasculară 160 Semiologie bănuiţi că ar avea HTA prin exces de . Sindromul Cushing mineralocorticoizi, la
  - `cushing`: 5 matches
    - page=2 section=unknown chunk_id=a21c788a44bcbc9a hits=1 preview=Pneumonia interstiţială acută ......................................... 88 Alte cauze de leziuni pulmonare int
    - page=5 section=MAC =MAC; chunk_id=4fee367ea5b03c61 hits=1 preview=RRVS = radiografie renovezicală simplă; MAT= microangiopatie trombotică; RVPu = rezistenţei vasculare pulmonar
    - page=41 section=(1/4 C.V.). chunk_id=1883dc11a5ba71b9 hits=1 preview=• sindrom adipozogenital, • sindrom Cushing, • sonoritate normală +- aerul conţinut în mod • tratament cu digo
  - `hipercortizolism`: 0 matches

## Retrieval Probes

- `sindromul cushing` -> error: Unexpected Response: 400 (Bad Request)
Raw response content:
b'{"status":{"error":"Wrong input: Vector dimension error: expected dim: 768, got 384"},"time":0.008372762}'
- `colesterol embolii placi ateromatoase` -> error: Unexpected Response: 400 (Bad Request)
Raw response content:
b'{"status":{"error":"Wrong input: Vector dimension error: expected dim: 768, got 384"},"time":0.001146533}'
- `insuficienta cardiaca simptome` -> error: Unexpected Response: 400 (Bad Request)
Raw response content:
b'{"status":{"error":"Wrong input: Vector dimension error: expected dim: 768, got 384"},"time":0.00172461}'

## Notes

- This baseline is intended for before/after comparison once E7.1 fallback tuning is complete.
- If retrieval probes show runtime errors, chunk keyword probes remain the source of truth for corpus presence.
