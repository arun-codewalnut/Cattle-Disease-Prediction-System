# STATE.md

Living snapshot of project state. Update this whenever you finish a meaningful chunk of work —
this is what an agent (or you) reads first when resuming.

_Last updated: 2026-09-17_

## Known gaps

- `shap`/`chromadb` need Microsoft C++ Build Tools to install natively on Windows (Python 3.13
  has no prebuilt wheels yet) — works fine inside Docker (`make up`). See
  [ml-service/AGENTS.md](ml-service/AGENTS.md).
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
- **M5 done** (issue #5, branch `feat/m5-langgraph-agent-orchestration`, branched from
  `main`): `run_diagnosis()` is now a real LangGraph `StateGraph`
  (`intake → route → predict_symptoms|predict_image → explain → recommend`) instead of one
  plain function. `explain` node generates real LLM text via `app/agent/llm.py`'s
  provider-swappable `get_llm()` (Ollama by default), falling back to the old deterministic
  template on any LLM failure — diagnosis, confidence, and the `REPORTABLE_DISEASES`
  escalation rule are all byte-for-byte unchanged from M1/M2 (deliberately — this milestone
  improves explanation quality, not diagnostic accuracy, see `docs/DECISIONS.md`).
  `image_url` now routes to a clear `NOT_IMPLEMENTED` (501) instead of being silently
  ignored. New dependency `langchain-ollama==0.2.2` (version-pinned for compatibility with
  the existing `langchain-core==0.3.28`). 21/21 ml-service tests passing (6 new). Found and
  fixed a real test-suite performance bug: without mocking, every confident-diagnosis test
  tried to actually reach Ollama (not installed here) and waited out a connection timeout —
  15 tests went from ~2s to ~25s; fixed with an autouse `conftest.py` fixture that fails
  fast by default (the honest reflection of this environment having no LLM available),
  back to ~2s for 21 tests.
- Full-application build+test re-verified at every milestone: `ml-service` pytest,
  `frontend` vitest + production build, `backend` `mvn test` (needs Postgres — fixed CI to
  provide one via a service container).

## In Progress

- M5 not yet committed/PR'd (still on `feat/m5-langgraph-agent-orchestration`).

## Not Started

- M6: RAG knowledge base (Chroma)
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
