# Playbook: Run the full stack locally

## Option A — Docker Compose (both services in one command)

1. Copy each service's `.env.example` to `.env` (the defaults work as-is; compose requires
   both files to exist).
2. From the repo root: `make up` (wraps `docker compose up --build`).
   - Starts: `ml-service` (FastAPI, port 8000 — also serves the public `/api/diagnoses*`
     endpoints the UI calls) and `frontend` (Vite dev server, port 5173). No databases — both were removed, see
     `docs/specs/remove-databases.md`.
3. **No training step**: the trained models are committed in `ml-service/models/`, so a
   fresh clone diagnoses straight away. Retraining is optional — README's "Retraining
   models" section and each `ml-service/data/*/SOURCE.md`.
4. Verify each service:
   - `ml-service`: `curl http://localhost:8000/health` → `{"status":"ok"}`
   - `frontend`: open `http://localhost:5173`
5. Tear down: `make down`.

## Option B — native (faster iteration; full functionality)

The same **required one-time model training** as Option A step 3 applies here, run from
`ml-service/` with the venv active instead of through the container:
`python -m training.generate_synthetic_data && python -m training.symptom_model_train`.

- `frontend`: `cd frontend && npm install` once, then `npm run dev`
- `ml-service`: `cd ml-service && .venv\Scripts\python -m uvicorn app.main:app --reload`
  — everything installs cleanly from wheels (no C++ compiler needed), and this
  is full functionality: precautions, next steps and citations all work, since the reference
  documents are read straight from `data/veterinary-reference/`.

## Running ml-service's own tests

`pytest` from `ml-service/`. The whole suite runs natively with no skips — the RAG tests
used to need Docker because of `chromadb`, which is gone (`docs/specs/remove-databases.md`).
