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
