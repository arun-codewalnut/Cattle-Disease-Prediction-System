# Playbook: Run the full stack locally

## Option A — Docker Compose (recommended; only way to get RAG-grounded explanations)

1. Copy each service's `.env.example` to `.env` (defaults work for local Docker Compose —
   Postgres credentials are dev-only placeholders).
2. From the repo root: `make up` (wraps `docker compose up --build`).
   - Starts: Postgres, `ml-service` (FastAPI, port 8000), `backend` (Spring Boot, port
     8080), `frontend` (Vite dev server, port 5173). (The `chroma` service in
     `docker-compose.yml` is currently unused — M6 uses Chroma embedded inside `ml-service`
     instead. See `docs/DECISIONS.md`.)
3. **One-time, required**: train the Cow symptom model. Model artifacts are gitignored, so a
   fresh clone has none and *every* diagnosis returns `503 MODEL_NOT_TRAINED`. This is the
   only model that needs no downloaded dataset; the bind mount puts the artifact in
   `ml-service/models/` on the host, so it survives `make down` and rebuilds:
   ```bash
   docker compose run --rm ml-service python -m training.generate_synthetic_data
   docker compose run --rm ml-service python -m training.symptom_model_train
   ```
   Other models (Sheep symptoms, cattle/cat/dog images) each need a real dataset first —
   see the matching `ml-service/data/*/SOURCE.md` and README's "Training/retraining a model".
4. **One-time, optional**: ingest the RAG knowledge base (needed for `sources`/grounded
   explanations to actually populate — skip this and the app still works, just without that
   part):
   ```bash
   docker compose run --rm ml-service python -m app.rag.ingest
   ```
5. Verify each service:
   - `ml-service`: `curl http://localhost:8000/health` → `{"status":"ok"}`
   - `backend`: `curl http://localhost:8080/actuator/health` → `{"status":"UP"}`
   - `frontend`: open `http://localhost:5173`
6. Tear down: `make down`.

## Option B — native (faster iteration; RAG grounding gracefully disabled)

The same **required one-time model training** as Option A step 3 applies here, run from
`ml-service/` with the venv active instead of through the container:
`python -m training.generate_synthetic_data && python -m training.symptom_model_train`.

- `frontend`: `cd frontend && npm install` once, then `npm run dev`
- `backend`: `cd backend && mvn spring-boot:run` (needs a real Postgres reachable —
  `docker run -d -e POSTGRES_DB=cattlecare -e POSTGRES_USER=cattlecare -e POSTGRES_PASSWORD=cattlecare -p 5432:5432 postgres:16-alpine`,
  or `make up` just for that one service)
- `ml-service`: `cd ml-service && .venv\Scripts\activate && uvicorn app.main:app --reload`
  — **`chromadb` and `shap` can't install natively on Windows/Python 3.13 without
  Microsoft C++ Build Tools** (no prebuilt wheel for either there; `chroma-hnswlib` has no
  `cp313` wheel at all — confirmed via PyPI, not just "needs Build Tools" — see
  `ml-service/AGENTS.md`). Skip both and install the rest; README has the exact filter
  command. The app still runs and diagnoses correctly without them —
  `retrieve()` catches the missing-dependency error and degrades to `sources: []`, same as
  any other retrieval failure. You only lose M6's grounded-explanation citations, nothing
  else breaks.

## Running ml-service's own tests

- Non-RAG tests: native venv, `pytest` from `ml-service/` — works fine without `chromadb`.
- RAG tests (`test_rag_retrieval.py`, and the RAG-touching cases in `test_agent_graph.py`):
  need Docker — see `ml-service/AGENTS.md` for the exact build/run commands (includes a fix
  for a network issue that corrupted the image build in this environment).
