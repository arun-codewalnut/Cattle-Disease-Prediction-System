# STATE.md

Living snapshot of project state. Update this whenever you finish a meaningful chunk of work —
this is what an agent (or you) reads first when resuming.

_Last updated: 2026-09-18 (session 5)_

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
- **M9 PR merged to `main`** (issue #18 stays open — only the spec-written acceptance
  criterion was satisfied, per that PR's own scope).
- **M10 done, not yet merged** (issue #19, branch `feat/m10-precautions-next-steps`,
  branched from synced `main`): every diagnosis now returns `precautions`/`next_steps`
  alongside `explanation`. **Deliberately not LLM-generated** — looked up verbatim from the
  veterinary-reference docs via a new exact `(disease, section)` match
  (`get_precautions()`), never a similarity search, so it can never soften the
  `REPORTABLE_DISEASES` escalation rule. The 4 existing disease docs got new
  `## Precautions`/`## Next steps` sections; a new `healthy.md` covers the `Healthy` case
  (didn't need reference material before this). `app/rag/ingest.py` now tags each chunk
  with a `section` metadata field; `retrieve()` (used for the LLM-grounded `explanation`)
  is now filtered to `section: overview` only, so the two kinds of content never mix — a new
  regression test locks this in. New `add_precautions` LangGraph node between `explain` and
  `recommend`. Threaded through `backend` (`DiagnosisResult`/`DiagnosisCaseResponse`, live in
  the response, not persisted — same precedent as `explanation`) and `frontend`
  (`DiagnosisResult.jsx`, new "🛡️ Precautions"/"📋 Next steps" sections). Spec:
  [docs/specs/M10-precautions-next-steps.md](docs/specs/M10-precautions-next-steps.md).
  **Validated three ways**: ml-service native 36/2 (skipped), ml-service **in Docker with
  real chromadb 48/48** (including the reportable-disease escalation-wording test and the
  retrieve()-isolation regression test), backend 15/15, frontend lint + 7/7 + build all
  green, **plus live end-to-end verification** — ran ml-service in Docker against the real
  re-ingested Chroma collection, backend and frontend natively, submitted real FMD symptoms
  in a real browser and confirmed real, escalation-consistent precautions/next-steps
  rendered. (One false alarm along the way: an em-dash that looked mangled in a `curl | python`
  verification command turned out to be that command's own console-encoding artifact, not an
  app bug — confirmed by forcing UTF-8 mode and re-checking.)
- **M10 PR merged to `main`** (issue #19) — confirmed via `git pull` before branching for M11.
- **M11 done, not yet merged** (issue #20, branch `feat/m11-buffalo-disease-detection`,
  branched from synced `main`): Buffalo added as a second species, with two significant
  design decisions made and logged (`docs/DECISIONS.md`), not deferred:
  1. **Renamed `Cattle` → `Animal` throughout `backend`** — entity/repository/service/
     controller/DTOs (package `.cattle` → `.animal`), `POST /api/cattle` →
     `POST /api/animals`, `diagnosis_case.cattle_id` → `animal_id`, error codes
     `CATTLE_NOT_FOUND`/`CATTLE_TAG_DUPLICATE` → `ANIMAL_NOT_FOUND`/`ANIMAL_TAG_DUPLICATE`.
     New Flyway migration (`V2__rename_cattle_to_animal.sql`, `V1__init.sql` untouched).
     Done now rather than deferred, since M12–M14 (Sheep/Cat/Dog) would otherwise repeat
     this exact discussion. Breaking API change, no versioning ceremony — acceptable per
     the standing local/learning-project position in `docs/DECISIONS.md`.
  2. **Buffalo diagnosis reuses the existing cattle-trained symptom model**, explicitly
     disclosed in the UI — no buffalo-specific dataset was found (same wall M9 hit for
     cattle images; confirmed via web research, not assumed, that FMD and LSD both affect
     buffalo, though LSD susceptibility is documented as lower than in cattle). `species`
     (`COW`/`BUFFALO`, `@Enumerated(STRING)`, extensible) is captured on the `Animal` record
     and shown in the UI but **not forwarded to ml-service** — no per-species model exists
     yet to justify threading it further.
  Also: `GlobalExceptionHandler` gains a proactive fix for malformed JSON / invalid enum
  values (`HttpMessageNotReadableException`) — the same raw-exception-leak bug class fixed
  reactively in M8, caught here before a user hit it, since an invalid `species` string is
  the first thing that could trigger it. Frontend: `AnimalIdentityFields` (renamed from
  `CattleIdentityFields`) gets a species `<select>`; a visible disclosure renders whenever
  a non-`COW` species is chosen. Spec:
  [docs/specs/M11-buffalo-disease-detection.md](docs/specs/M11-buffalo-disease-detection.md).
  **Validated**: backend 17/17 (clean build, migration applies correctly), ml-service
  unaffected (36/2 skipped, no ml-service files touched), frontend lint + 9/9 + build all
  green, **plus live end-to-end verification**: created a Buffalo animal via
  `POST /api/animals` in a real browser, confirmed the species disclosure rendered,
  submitted symptoms, and confirmed the diagnosis correctly escalated (`Foot and Mouth
  Disease`, `escalate_to_vet`) using the shared model exactly as designed — plus a direct
  `curl` check of the new `INVALID_REQUEST_BODY` error path.

## In Progress

- M11 (issue #20) — implementation done, PR not yet opened/merged.

## Not Started

- M7: Notifications (email/WhatsApp free tier)
- M9 real implementation (issue #18 still open — only the spec landed; training itself is
  blocked on the Kaggle dataset, see HANDOFF.md's Blockers)
- M12–M14: Sheep, Cat, Dog (issues #21–#23) — can now reuse M11's species-architecture
  pattern without re-litigating it (per that spec's own intent)

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
