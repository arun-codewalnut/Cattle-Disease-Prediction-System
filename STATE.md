# STATE.md

Living snapshot of project state. Update this whenever you finish a meaningful chunk of work —
this is what an agent (or you) reads first when resuming.

_Last updated: 2026-09-18 (session 3)_

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

- **Frontend UI redesign done, merged to `main`** (issue #15, PR #17): cattle/farm
  visual theme (CSS-gradient sky + hills + sun, inline-SVG only, no downloaded imagery),
  fully responsive (mobile/tablet/desktop, verified in a real browser at 375/768/1440px),
  colorful palette with light+dark variants, hover/focus-visible states on every input, emoji
  icons on every symptom field and the two identity fields, and an urgency-coded results card
  (🚨 red / 🩺 amber / 👀 green) for the three `recommendedAction` values. Purely
  presentational — no backend/ml-service change. Spec:
  [docs/specs/frontend-ui-redesign.md](docs/specs/frontend-ui-redesign.md).
- **M8 phase 1 done, not yet merged** (issue #16, branch `feat/m8-image-diagnosis-pipeline`,
  branched from `main` after the #15 merge): `predict_image` in `ml-service` returns a
  deterministic hash-based placeholder instead of `501`, routed through the same
  `explain`/`recommend` path as symptom-based diagnoses so `REPORTABLE_DISEASES` escalation
  applies identically — verified live (a placeholder result correctly escalated). New
  `POST /api/cattle/{cattleId}/diagnoses/image` on `backend` (multipart, JPEG/PNG, ≤5MB,
  base64-encoded and forwarded to ml-service as `image_base64`) — **images are never
  persisted to disk**, a deliberate scope decision (see spec). Frontend: new
  `ImageUploadForm` alongside the symptom checklist, sharing identity fields via a new
  `CattleIdentityFields` component. Spec:
  [docs/specs/M8-image-diagnosis-phase1.md](docs/specs/M8-image-diagnosis-phase1.md).
  ml-service 29/2 (skipped), backend 15/15, frontend 7/7 + lint + build all green.
- **Found and fixed two real bugs live** while manually testing M8 (user hit the second one
  in actual use): (1) splitting the identity fields into a shared component moved them
  outside both `<form>` elements, silently disabling native `required`-field validation for
  both symptom and image submission — fixed with explicit validation in `DiagnosisIntake.jsx`
  before either submit path fires. (2) `GlobalExceptionHandler` had no handler for
  `MethodArgumentNotValidException`, so a blank tag number returned the raw Spring exception
  (internal class names and all) as the error message — fixed with a proper
  `VALIDATION_FAILED` mapping (`{code, message, details: {field: reason}}`), covered by a new
  `CattleControllerTest` (this repo's first `@WebMvcTest`-based controller test — required
  `WebMvcTest`/`MockitoBean` from their new Spring Boot 4 packages, not the deprecated
  Boot-3-era ones).
- **Six new milestones/issues created (M9–M14)**, after researching real candidate datasets
  (found via web search, not guessed): M9 trains a real cattle image classifier on a
  Kaggle 3-class dataset (Healthy/LSD/FMD, 3,244 images), replacing M8's placeholder; M10
  adds RAG-grounded precautions/next-steps to every diagnosis (species-agnostic, benefits
  the existing cattle flow immediately); M11–M14 add Buffalo, Sheep, Cat, and Dog per the
  user's request — M11 is where the domain model first generalizes beyond "Cattle" (an open
  design question flagged in that issue, not decided yet), and M13 (Cat) is a real pivot from
  livestock to companion-animal diseases, flagged for its own `DISCLAIMER.md` review.
  `docs/ROADMAP.md` updated to list all six.
- **M8 phase 1 merged to `main`** (issue #16, PR #24) — confirmed via `git pull` before
  branching for M9.
- **M9 spec written, blocked on data** (issue #18, branch `feat/m9-cattle-image-classifier`):
  approach agreed (transfer learning on a pretrained torchvision backbone — new `torch`/
  `torchvision` deps — fine-tuning only the classifier head; scope limited to the 3 classes
  the candidate Kaggle dataset actually has: Healthy/LSD/FMD, explicitly not the symptom
  model's other 2). **Blocked**: no Kaggle account/API token in this environment, and unlike
  M1's synthetic-tabular-data fallback, there's no honest synthetic fallback for images — a
  procedurally-generated "photo" would teach a CNN nothing real. Nothing past the spec
  happens until the dataset is actually available locally. Spec:
  [docs/specs/M9-cattle-image-classifier.md](docs/specs/M9-cattle-image-classifier.md).
  Baseline re-verified unaffected before starting: ml-service 29/2 (skipped), backend 15/15,
  frontend 7/7 + lint + build, all green — this session's change is docs-only.

## In Progress

- M9 (issue #18) — spec written and blocked on the dataset; no code changes yet.

## Not Started

- M7: Notifications (email/WhatsApp free tier)
- M10: diagnosis precautions/next-steps (issue #19)
- M11–M14: Buffalo, Sheep, Cat, Dog (issues #20–#23)

Deployment (formerly M8 in the original numbering) was dropped from scope — see
`docs/DECISIONS.md`. The M8 number was reused for image-based disease recognition, a
deliberate, discussed reassignment — not a collision.

Full roadmap: [docs/ROADMAP.md](docs/ROADMAP.md).

## Key Decisions

See [docs/DECISIONS.md](docs/DECISIONS.md) for the full log. Summary:

- Polyglot split: Java (Spring Boot) for backend/business logic, Python (FastAPI + LangGraph)
  for ML/agent, React for UI — matches existing skills, keeps ML ecosystem in Python.
- Free/open-source only: Ollama (local LLM) or free API tiers, Chroma (vector DB), Flyway
  (migrations), free-tier hosting (Render/Railway/Vercel/Supabase).
- Agent orchestration lives in `ml-service` (LangGraph is Python-native); Java stays a
  conventional REST backend that calls into it.
