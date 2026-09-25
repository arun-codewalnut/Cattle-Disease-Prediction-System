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
- **Structure**: `app/api/` = FastAPI routers, `app/agent/` = LangGraph graph + tools,
  `app/models/` = ML inference wrappers, `app/rag/` = retrieval over
  `data/veterinary-reference/*.md`. Still RAG — the explain node grounds its prompt in
  retrieved documents; only the retrieval source is the filesystem rather than a vector
  store. No ingest step: edit a document, restart the service.
- **Tests**: `pytest` from `ml-service/` — the **whole** suite runs natively, no Docker and
  no skips. Keep unit tests here; cross-service flow tests go in the root `tests/e2e/`.
- **Correlation ID**: read from `request.state.correlation_id` (set by
  `app/middleware.py`) — always include it when logging.
- **LLM provider**: `app/agent/llm.py`'s `get_llm()` is the *only* place that should know
  which provider is in use — never instantiate `ChatOllama` (or any provider) directly
  elsewhere. Controlled by `LLM_PROVIDER`/`OLLAMA_BASE_URL`/`OLLAMA_MODEL` in `.env.example`.
  Ollama isn't installed in this dev environment by default — the `explain` node falls back
  to a deterministic template whenever the LLM call fails for any reason, so the app works
  fully without it. To see real LLM-generated explanations locally: install
  [Ollama](https://ollama.com/download), run `ollama pull llama3.1`, then `ollama serve`
  (or just launch the Ollama app) before starting `ml-service`.
