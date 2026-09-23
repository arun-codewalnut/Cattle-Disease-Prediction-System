@../AGENTS.md

## ml-service-specific conventions

- **Setup**: `py -m venv .venv`, then `.venv\Scripts\python -m pip install -r requirements.txt`,
  then `uvicorn app.main:app --reload`.
- **Native install caveat**: `shap` needs to compile a native extension and has no cp313
  wheel on Windows, so a bare `pip install -r requirements.txt` fails there without
  [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
  `shap` isn't imported anywhere (M1 uses XGBoost's own `pred_contribs` — see
  `docs/DECISIONS.md`), so installing everything except it is the practical workaround; the
  README has the exact command. **`chromadb`/`chroma-hnswlib` used to be the bigger blocker
  and is gone** — retrieval reads markdown directly now
  (`docs/specs/remove-databases.md`), which is why the tests no longer need Docker.
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
