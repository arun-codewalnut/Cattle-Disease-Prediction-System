@../AGENTS.md

## ml-service-specific conventions

- **Setup**: `py -m venv .venv`, then `.venv\Scripts\python -m pip install -r requirements.txt`,
  then `uvicorn app.main:app --reload`.
- **Known local-environment gap — confirmed, not just suspected**: `shap` and
  `chroma-hnswlib` (a `chromadb` dependency, needed since M6) need to compile native
  extensions, and there is **no `cp313` wheel at all**, any platform, for `chroma-hnswlib`
  as of its latest PyPI release (0.7.6 — checked directly, not assumed). Installing natively
  on Windows needs
  [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
  first (free, but a real system install). Until you've done that, `pip install chromadb`
  fails natively in this venv — **run `ml-service`'s tests via Docker instead** (the
  `Dockerfile` already has `build-essential`; from the repo root, in Git Bash on Windows the
  `MSYS_NO_PATHCONV=1` + `//app` avoids Git Bash mangling the container path into a Windows
  one):
  ```bash
  docker build -t ml-service-test ./ml-service
  MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd)/ml-service:/app" -w //app ml-service-test python -m pytest -v
  ```
  If the image build itself fails with `Hash Sum mismatch` on `apt-get install` (a
  network/proxy corrupting plain-HTTP `.deb` downloads — the *expected* hash stays the same
  across retries but the *received* content differs each time, confirmed while building
  this exact image), the `Dockerfile` already forces `https://deb.debian.org` to route
  around it — if you still hit this on a different network, that's the fix to look at.

  `shap` itself isn't actually imported anywhere in the code (M1 uses XGBoost's own
  `pred_contribs` instead — see `docs/DECISIONS.md`), so only `chromadb`/`chroma-hnswlib`
  is the real native-build blocker as of M6.
- **Structure**: `app/api/` = FastAPI routers, `app/agent/` = LangGraph graph + tools,
  `app/models/` = ML inference wrappers, `app/rag/` = Chroma ingestion + retrieval
  (`chromadb.PersistentClient`, embedded — not the separate networked `chroma` service in
  `docker-compose.yml`, which is unused as of M6, see `docs/DECISIONS.md`).
- **Tests**: `pytest` from `ml-service/` (native venv — works for everything except RAG,
  see the Docker note above). Keep unit tests here; cross-service flow tests go in
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
