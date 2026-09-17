@../AGENTS.md

## ml-service-specific conventions

- **Setup**: `py -m venv .venv`, then `.venv\Scripts\python -m pip install -r requirements.txt`,
  then `uvicorn app.main:app --reload`.
- **Known local-environment gap**: `shap` and `chroma-hnswlib` (a `chromadb` dependency) need
  to compile native extensions, and Python 3.13 doesn't yet have prebuilt Windows wheels for
  them. Installing them requires
  [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
  (free) first. They're commented out of the working install until then — needed for M1
  (SHAP explainability) and M6 (Chroma RAG), not before.
- **Structure**: `app/api/` = FastAPI routers, `app/agent/` = LangGraph graph + tools,
  `app/models/` = ML inference wrappers, `app/rag/` = Chroma setup/retrieval.
- **Tests**: `pytest` from `ml-service/`. Keep unit tests here; cross-service flow tests go in
  the root `tests/e2e/`.
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
