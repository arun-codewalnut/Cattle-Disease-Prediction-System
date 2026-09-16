# Playbook: Run the full stack locally

1. Copy each service's `.env.example` to `.env` and fill in local values (defaults work for
   local Docker Compose — Postgres/Chroma credentials are dev-only placeholders).
2. From the repo root: `make up` (wraps `docker compose up --build`).
   - Starts: Postgres, Chroma, `ml-service` (FastAPI, port 8000), `backend` (Spring Boot,
     port 8080), `frontend` (Vite dev server, port 5173).
3. Verify each service:
   - `ml-service`: `curl http://localhost:8000/health`
   - `backend`: `curl http://localhost:8080/actuator/health`
   - `frontend`: open `http://localhost:5173`
4. Tear down: `make down`.

Running a single service without Docker (faster iteration while developing):
- `frontend`: `cd frontend && npm run dev`
- `backend`: `cd backend && mvn spring-boot:run`
- `ml-service`: `cd ml-service && .venv\Scripts\activate && uvicorn app.main:app --reload`
