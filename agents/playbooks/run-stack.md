# Playbook: Run the full stack locally

## Option A — Docker Compose (all three services in one command)

1. Copy each service's `.env.example` to `.env` (the defaults work as-is; compose requires
   all three files to exist).
2. From the repo root: `make up` (wraps `docker compose up --build`).
   - Starts: `ml-service` (FastAPI, port 8000), `backend` (Spring Boot, port 8080),
     `frontend` (Vite dev server, port 5173). No databases — both were removed, see
     `docs/specs/remove-databases.md`.
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
4. Verify each service:
   - `ml-service`: `curl http://localhost:8000/health` → `{"status":"ok"}`
   - `backend`: `curl http://localhost:8080/actuator/health` → `{"status":"UP"}`
   - `frontend`: open `http://localhost:5173`
5. Tear down: `make down`.

## Option B — native (faster iteration; full functionality)

The same **required one-time model training** as Option A step 3 applies here, run from
`ml-service/` with the venv active instead of through the container:
`python -m training.generate_synthetic_data && python -m training.symptom_model_train`.

- `frontend`: `cd frontend && npm install` once, then `npm run dev`
- `backend`: `cd backend && mvn spring-boot:run` (stateless — nothing to provision)
- `ml-service`: `cd ml-service && .venv\Scripts\activate && uvicorn app.main:app --reload`
  — everything installs cleanly from wheels (no C++ compiler needed), and this
  is full functionality: precautions, next steps and citations all work, since the reference
  documents are read straight from `data/veterinary-reference/`.

## Running ml-service's own tests

`pytest` from `ml-service/`. The whole suite runs natively with no skips — the RAG tests
used to need Docker because of `chromadb`, which is gone (`docs/specs/remove-databases.md`).
