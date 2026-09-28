# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-28, part 2) — Two-screen diagnosis UI

Branch `feat/two-screen-diagnosis-ui` (branched from `feat/goat-and-species-symptom-models`,
so it includes the Goat PPR change — merge that one first, or merge this one alone to get
both). Spec: `docs/specs/two-screen-diagnosis-ui.md`.

- **Symptoms | Photo tabs** (real ARIA tab list, arrow keys work). Symptoms lists Cow, Sheep,
  Goat; Photo lists all five.
- **Layout**: form centred until submit; then the result pane grows in on the right and the
  form glides left (CSS only, ~0.6s, off under reduced motion); below 900px the result stacks
  under the form and the page scrolls to it. Loading skeleton and API errors appear in the
  result area.
- Fixed along the way: the "Escalate to vet" action box is now tinted with the card's
  urgency colour (was always green); alert text uses the theme token, so it's readable in
  dark mode.
- **Gotcha for local dev**: Vite inside Docker on Windows doesn't see file changes through
  the bind mount — `docker compose restart frontend` after editing, or run `npm run dev`
  natively.

## This session (2026-09-28) — Goat PPR symptom screen + symptom-dataset search

Branch `feat/goat-and-species-symptom-models`. Spec: `docs/specs/goat-ppr-symptom-screen.md`.

- **Goat can now be diagnosed from symptoms** — the same PPR screen as Sheep (routing entry in
  `app/agent/graph.py`, `GOAT` added to `SYMPTOM_SUPPORTED_SPECIES`, Goat gets the PPR
  checklist in the frontend and keeps its photo model).
- **Why it's valid for goats**: the PPR model's accuracy was measured per `animal` code
  (undecodable goat/sheep column) with the training script's own 5-fold setup — 80.0% and
  80.7%, PPR recall 78.9% and 87.9%.
- **Dataset search**: seven Kaggle candidates for Sheep/Goat/Cat/Dog symptom data inspected
  and rejected (generated data with impossible labels, no disease column, or too small and
  contradictory) — reasons per dataset in the spec. Cat/Dog stay symptom-blocked per owner.

## Previous session (2026-09-27) — Java backend merged into ml-service

Branch `feat/merge-backend-into-ml-service`. Spec (read this first — it's the source of truth
for every status/error code): `docs/specs/merge-backend-into-ml-service.md`. Decision entry:
"Java backend merged into ml-service" at the end of `docs/DECISIONS.md`.

- **Two services now**: `frontend` (:5173) and `ml-service` (:8000). `backend/` (Spring Boot
  gateway) is deleted. Its public endpoints `POST /api/diagnoses` and
  `POST /api/diagnoses/image` live in `ml-service/app/api/diagnoses.py` and call the agent
  in-process — same paths, status codes, camelCase fields and error codes. The frontend's
  `VITE_API_BASE_URL` default is now `http://localhost:8000`.
- **Deliberate differences** (all four in the spec): `ML_SERVICE_ERROR`/`ML_SERVICE_UNAVAILABLE`
  retired (agent errors like `MODEL_NOT_TRAINED` 503 reach the caller directly); total upload
  cap raised to 5 × 5MB (+1MB); non-JSON body on the symptom endpoint → `INVALID_REQUEST_BODY`
  (was `IMAGE_REQUIRED`); `/actuator/health` gone, `GET /health` only.
- **CORS** is now configured in `ml-service` from `CORS_ALLOWED_ORIGINS` (comma-separated,
  default `http://localhost:5173`).
- **Tests**: the JUnit suite's behaviour is carried over as pytest in
  `ml-service/tests/test_public_api.py`; CI has two jobs (frontend, ml-service); the
  pre-commit hook has no Maven step.
- **Docs**: all current-state docs (README, AGENTS/CLAUDE files, ARCHITECTURE, API_CONTRACTS,
  REPO_MAP, TESTING, ROADMAP, playbooks, run-stack skill, GitHub templates, e2e README) updated
  to the two-service layout. Historical specs in `docs/specs/` and older DECISIONS entries
  deliberately still describe the Java backend.

### Same session, second pass — Ollama removed, one install, .env examples, README rewrite

- **Ollama/LLM path removed** (spec `docs/specs/remove-ollama.md`): `app/agent/llm.py`,
  `retrieve()`, `langchain-ollama` and the `LLM_*`/`OLLAMA_*` settings are gone; `explain`
  always uses the template. Verified byte-identical output on 15 representative diagnoses
  before/after (the template was already the only path that ran anywhere).
- **`ml-service/requirements.txt` is the complete install** — now also `numpy`, `pillow`
  (imported directly, were only transitive), `kagglehub`, `roboflow`. Verified with a
  brand-new venv: one `pip install -r requirements.txt`, `pip check` clean, full suite passes.
  Windows gotcha found doing that: a deeply nested clone path breaks the torch install
  (260-char path limit) — documented in README.
- **`.env.example` everywhere settings are read**: `ml-service/` (`CORS_ALLOWED_ORIGINS`,
  `ROBOFLOW_API_KEY`, `PORT`), `frontend/` (`VITE_API_BASE_URL`), and new `tests/e2e/`
  (`FRONTEND_URL`, `ML_SERVICE_URL`, loaded by `playwright.config.js` via Node's
  `process.loadEnvFile`).
- **Leftover `backend/` folder deleted** from disk (it only held an ignored `.env`).
- **README rewritten** for someone who just cloned the repo: what it does, species table,
  what to install (Python 3.13 + Node 22.12+), quick start, `.env` reference, API, tests,
  retraining. Architecture diagram no longer shows email/WhatsApp notifications as built
  (M7 is still open).
- **One-command dataset download**: `python -m training.fetch_datasets` pulls every Kaggle
  dataset into the right `data/` folders (skips folders that already have files; long-path
  safe on Windows; drops `desktop.ini`-style clutter). Verified: into an empty folder it
  produces the same file names as the existing `data/` for all 13 class folders, and the
  Sheep CSV is byte-identical. `goat-images/SOURCE.md` was never pushed (missing
  `.gitignore` exception) — fixed.

## Next session

- **Railway follow-up once this merges** (dashboard, owner action — not doable from the repo):
  1. Delete the `java` service.
  2. On the `frontend` service, set `VITE_API_BASE_URL` to `ml-service`'s **public** URL
     (the browser calls it directly now; the private `ml-service.railway.internal` hostname
     is no longer used by anything).
  3. On `ml-service`, set `CORS_ALLOWED_ORIGINS` to the frontend's public URL.
  4. Smoke-test one symptom and one photo diagnosis through the deployed UI.
- Still-open items carried over from earlier sessions, unchanged: Cow Mastitis precision
  (~41%) — more clean data is the real fix; the unreviewed ~168-image Roboflow bucket; Dog's
  ~13% combined block rate; Goat's placeholder-image contamination; the "temp"-not-humanized
  Sheep explanation wording; the diagram/chart gate's disclosed remaining gap.

## Blockers

- None. (The Railway steps above are follow-ups, not blockers for merging.)
