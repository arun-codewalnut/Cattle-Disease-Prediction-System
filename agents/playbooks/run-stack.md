# Playbook: Run the full stack locally

## Option A — Docker Compose (recommended; only way to get RAG-grounded explanations)

1. Copy each service's `.env.example` to `.env` (defaults work for local Docker Compose —
   Postgres credentials are dev-only placeholders).
2. From the repo root: `make up` (wraps `docker compose up --build`).
   - Starts: Postgres, `ml-service` (FastAPI, port 8000), `backend` (Spring Boot, port
     8080), `frontend` (Vite dev server, port 5173). (The `chroma` service in
     `docker-compose.yml` is currently unused — M6 uses Chroma embedded inside `ml-service`
     instead. See `docs/DECISIONS.md`.)
3. **One-time**: ingest the RAG knowledge base (needed for `sources`/grounded explanations
   to actually populate — skip this and the app still works, just without that part):
   ```bash
   docker compose run --rm ml-service python -m app.rag.ingest
   ```
4. Verify each service:
   - `ml-service`: `curl http://localhost:8000/health`
   - `backend`: `curl http://localhost:8080/actuator/health`
   - `frontend`: open `http://localhost:5173`
5. Tear down: `make down`.

## Option B — native (faster iteration; RAG grounding gracefully disabled)

- `frontend`: `cd frontend && npm run dev`
- `backend`: `cd backend && mvn spring-boot:run` (needs a real Postgres reachable —
  `docker run -d -e POSTGRES_DB=cattlecare -e POSTGRES_USER=cattlecare -e POSTGRES_PASSWORD=cattlecare -p 5432:5432 postgres:16-alpine`,
  or `make up` just for that one service)
- `ml-service`: `cd ml-service && .venv\Scripts\activate && uvicorn app.main:app --reload`
  — **`chromadb` cannot install natively on Windows/Python 3.13** (no `cp313` wheel exists
  for `chroma-hnswlib`, confirmed via PyPI, not just "needs Build Tools" — see
  `ml-service/AGENTS.md`). The app still runs and diagnoses correctly without it —
  `retrieve()` catches the missing-dependency error and degrades to `sources: []`, same as
  any other retrieval failure. You only lose M6's grounded-explanation citations, nothing
  else breaks.

## Running ml-service's own tests

- Non-RAG tests: native venv, `pytest` from `ml-service/` — works fine without `chromadb`.
- RAG tests (`test_rag_retrieval.py`, and the RAG-touching cases in `test_agent_graph.py`):
  need Docker — see `ml-service/AGENTS.md` for the exact build/run commands (includes a fix
  for a network issue that corrupted the image build in this environment).
