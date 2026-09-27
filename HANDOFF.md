# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-27) — Java backend merged into ml-service

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
