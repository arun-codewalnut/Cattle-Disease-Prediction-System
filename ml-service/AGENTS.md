@../AGENTS.md

## ml-service-specific conventions

- **Setup**: `py -m venv .venv`, then `.venv\Scripts\python -m pip install -r requirements.txt`,
  then `uvicorn app.main:app --reload`.
- **No native builds**: every dependency installs from a prebuilt wheel on all platforms.
  Keep it that way — don't add a package that has to compile (no cp313 wheel) without a real
  need. `shap` was removed for exactly this (never imported; M1 uses XGBoost's own
  `pred_contribs` — see `docs/DECISIONS.md`), and `chromadb`/`chroma-hnswlib` before it
  (`docs/specs/remove-databases.md`). It's also why the Dockerfile needs no compiler.
- **Docker image**: the Dockerfile's CMD is the production one (honours `$PORT`, no
  `--reload`); `docker-compose.yml` overrides it with `--reload` for local dev.
  `.dockerignore` keeps `.venv/` and training datasets out of the image — only
  `data/veterinary-reference/` is read at runtime.
- **Public API**: `app/api/diagnoses.py` serves the frontend directly —
  `POST /api/diagnoses` and `POST /api/diagnoses/image` (validation, species rules, camelCase
  response shaping; calls the agent in-process via `run_in_threadpool`). `app/api/diagnose.py`
  (`POST /agent/diagnose`) is the internal agent endpoint; `GET /health` is the only health
  check. Errors go through `app/errors.py` (`ApiError` → `{code, message, details}`); keep that
  shape. Contract: `docs/API_CONTRACTS.md`, spec: `docs/specs/merge-backend-into-ml-service.md`.
- **CORS**: allowed origins come from `CORS_ALLOWED_ORIGINS` (comma-separated, default
  `http://localhost:5173`) in `app/main.py` — set it to the deployed frontend's URL.
- **Structure**: `app/api/` = FastAPI routers, `app/agent/` = LangGraph graph + tools,
  `app/models/` = ML inference wrappers, `app/rag/` = precautions/next-steps lookup from
  `data/veterinary-reference/*.md` (exact match by diagnosis, no vector store). No ingest
  step: edit a document, restart the service.
- **Tests**: `pytest` from `ml-service/` — the **whole** suite runs natively, no Docker and
  no skips. The public API's behaviour (every status/error code in the spec) is covered by
  `tests/test_public_api.py`. Keep unit tests here; cross-service flow tests go in the root `tests/e2e/`.
- **Correlation ID**: read from `request.state.correlation_id` (set by
  `app/middleware.py`) — always include it when logging.
- **Explanations**: the `explain` node always builds a deterministic template from the
  model's own output (`_template_explanation` in `app/agent/graph.py`) — no LLM. An optional
  Ollama path used to exist but never ran anywhere and was removed
  ([docs/specs/remove-ollama.md](../docs/specs/remove-ollama.md)). Adding an LLM back is a
  new spec, not a config switch.
