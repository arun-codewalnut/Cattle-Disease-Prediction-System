# STATE.md

Living snapshot of project state. Update this whenever you finish a meaningful chunk of work —
this is what an agent (or you) reads first when resuming.

_Last updated: 2026-09-17_

## Known gaps

- `chromadb`/`chroma-hnswlib` cannot install natively on Windows/Python 3.13 — confirmed no
  `cp313` wheel exists at all (any platform), not just "needs Build Tools." Verified working
  via Docker instead — see [ml-service/AGENTS.md](ml-service/AGENTS.md) for the exact build
  command (includes a fix for a network/proxy that was corrupting `apt-get`'s HTTP
  downloads — forced to HTTPS).
- `springdoc-openapi` Spring-Boot-4 compatibility unverified — not added to `backend/pom.xml`
  yet. See [backend/AGENTS.md](backend/AGENTS.md).
- No `LICENSE` file yet — open decision, not yet made.
- `tests/e2e` browsers not installed yet (`npx playwright install --with-deps chromium`,
  one-time) — smoke test scaffold works, hasn't been run against a live `make up` stack yet.
- Backend tests need a real Postgres running locally (not just `mvn compile`) — see
  `backend/AGENTS.md` for the one-line `docker run` to start one.

## Done

- Repo scaffolded: monorepo structure (`frontend/`, `backend/`, `ml-service/`), docs,
  agent-context files (`AGENTS.md`/`CLAUDE.md`/`STATE.md`/`HANDOFF.md`), Docker Compose,
  Makefile, CI skeleton.
- `backend` (Spring Boot 4.1.1) compiles, with `CorrelationIdFilter`, `GlobalExceptionHandler`
  (shared error shape), and a Flyway baseline migration.
- `ml-service` (FastAPI) has a working `/health` and stub `/agent/diagnose` endpoint,
  correlation-ID middleware — `pytest` passes.
- `frontend` (React 19 + Vite) scaffolded, `npm install` done.
- Governance layer: `CONTRIBUTING.md`, `docs/DISCLAIMER.md`,
  `.github/ISSUE_TEMPLATE/*`, `.github/PULL_REQUEST_TEMPLATE.md`.
- **12 agentic-engineering competencies implemented** (see `docs/DECISIONS.md` entry
  "Implemented CodeWalnut's 12 agentic-engineering competencies" for the full list):
  guardrail hooks + deny rules, `docs/specs/` + M1 spec, `docs/REPO_MAP.md`, Vitest +
  Playwright wired and passing, `retrospective` skill, Mermaid diagrams, real pre-commit
  hook, explicit code-review + token-economics guidance.
- Initial commit made and pushed to `origin/main`
  (github.com/arun-codewalnut/Cattle-Disease-Prediction-System).
- GitHub Milestones M1–M7 created with matching issues #1–#7 (via `gh` CLI — see
  `docs/DECISIONS.md`). M8 (deployment) dropped from scope entirely.
- **M1 done, merged to `main`** (issue #1, PR #8): baseline XGBoost symptom classifier —
  `ml-service/app/models/symptom_model.py` (`predict()`), `ml-service/training/`, 10/10
  tests passing. 5-fold CV: accuracy 0.888, macro F1 0.888. Synthetic dataset + XGBoost's
  native `pred_contribs` instead of `shap` — deliberate, documented deviations.
- **M2 done, merged to `main`** (issue #2, PR #9 + catch-up PR #10): `/agent/diagnose`
  calls the real M1 model. `REPORTABLE_DISEASES` escalation rule enforcing
  `docs/DISCLAIMER.md`. 15/15 tests passing.
- **M3 done, merged to `main`** (issue #3, PR #11): `Cattle`/`DiagnosisCase` JPA entities,
  `POST /api/cattle` + `POST /api/cattle/{id}/diagnoses`, `MlServiceClient` with structured
  error translation. 9/9 backend tests passing (8 new). Found and fixed: `RestClient.Builder`
  isn't auto-configured in this Spring Boot 4 setup — see `docs/DECISIONS.md`.
- **M4 done, merged to `main`** (issue #4, PR #12): React symptom-intake form → creates
  cattle → submits symptoms → rendered result with urgency styling + disclaimer. 3/3 Vitest
  tests. **Found and fixed two real integration bugs live** (CORS never configured on
  `backend`; JDK `HttpClient` HTTP/2-upgrade vs. uvicorn incompatibility) — see
  `docs/DECISIONS.md`. Verified end-to-end in a real browser.
- **M5 done, merged to `main`** (issue #5, PR #13): `run_diagnosis()` is a real LangGraph
  `StateGraph` (`intake → route → predict_symptoms|predict_image → explain → recommend`).
  `explain` generates real LLM text via `app/agent/llm.py`'s provider-swappable `get_llm()`
  (Ollama by default), falling back to a deterministic template on any LLM failure —
  diagnosis, confidence, and `REPORTABLE_DISEASES` unchanged from M1/M2 (deliberate —
  explanation quality, not diagnostic accuracy). `image_url` → `NOT_IMPLEMENTED` (501). New
  dep `langchain-ollama==0.2.2`. 21/21 tests. Found/fixed a test-suite perf bug (LLM
  connection timeouts without mocking, 15 tests ~2s→~25s, fixed via autouse fail-fast
  fixture).
- **M6 done** (issue #6, branch `feat/m6-rag-knowledge-base`, branched from `main`):
  `explain` node now retrieves grounding passages from a Chroma-backed knowledge base
  (`app/rag/`, embedded `chromadb.PersistentClient`, not the unused networked service in
  `docker-compose.yml`) before calling the LLM — `sources` field finally populated (only
  when actually used to ground a successful LLM explanation, `[]` otherwise). 4 original
  hand-written veterinary reference docs (`ml-service/data/veterinary-reference/`, same
  "not real sourced data" honesty as M1's dataset). **`chromadb` confirmed impossible to
  install natively on Windows/Python 3.13** (no `cp313` wheel exists, any platform) —
  verified via Docker instead: 29/29 ml-service tests passing. Found/fixed two real
  environment issues along the way: (1) a network/proxy corrupting `apt-get`'s plain-HTTP
  downloads (fixed by forcing HTTPS in the Dockerfile), and (2) Docker Desktop's daemon
  itself went unresponsive mid-build, needing a restart. See `docs/DECISIONS.md`.
- Full-application build+test re-verified at every milestone: `ml-service` pytest (native
  venv, or Docker for RAG-dependent tests since M6), `frontend` vitest + production build,
  `backend` `mvn test` (needs Postgres — fixed CI to provide one via a service container).

## In Progress

- M6 not yet committed/PR'd (still on `feat/m6-rag-knowledge-base`).

## Not Started

- M7: Notifications (email/WhatsApp free tier)

Deployment (formerly M8) was dropped from scope — see `docs/DECISIONS.md`.

Full roadmap: [docs/ROADMAP.md](docs/ROADMAP.md).

## Key Decisions

See [docs/DECISIONS.md](docs/DECISIONS.md) for the full log. Summary:

- Polyglot split: Java (Spring Boot) for backend/business logic, Python (FastAPI + LangGraph)
  for ML/agent, React for UI — matches existing skills, keeps ML ecosystem in Python.
- Free/open-source only: Ollama (local LLM) or free API tiers, Chroma (vector DB), Flyway
  (migrations), free-tier hosting (Render/Railway/Vercel/Supabase).
- Agent orchestration lives in `ml-service` (LangGraph is Python-native); Java stays a
  conventional REST backend that calls into it.
