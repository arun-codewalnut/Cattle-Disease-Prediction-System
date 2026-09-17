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
- **M4 done** (issue #4, branch `feat/m4-symptom-intake-ui`, branched from `main`): React
  symptom-intake form (11 checkboxes + tag/farm ID) → `POST /api/cattle` →
  `POST /api/cattle/{id}/diagnoses` → rendered result with urgency-appropriate styling and
  the "not a confirmed diagnosis" disclaimer. 3/3 Vitest component tests passing. **Found
  and fixed two real integration bugs by actually running the full stack and submitting the
  form in a live browser** (neither was catchable by mocked unit tests): (1) CORS was never
  configured on `backend` — added `WebConfig.java`; (2) the JDK `HttpClient` underlying
  `MlServiceClient` attempted an HTTP/2 upgrade that uvicorn rejects — pinned to HTTP/1.1
  explicitly. Both documented in `docs/DECISIONS.md`. Verified live end-to-end after fixing:
  real diagnosis (Foot and Mouth Disease, 98% confidence, "Escalate to vet") rendered
  correctly in the browser.
- Full-application build+test re-verified at every milestone: `ml-service` pytest,
  `frontend` vitest + production build, `backend` `mvn test` (needs Postgres — fixed CI to
  provide one via a service container).

## In Progress

- M4 not yet committed/PR'd (still on `feat/m4-symptom-intake-ui`).

## Not Started

- M5: LangGraph agent wiring (intake → predict → explain)
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
