# STATE.md

Living snapshot of project state. Update this whenever you finish a meaningful chunk of work —
this is what an agent (or you) reads first when resuming.

_Last updated: 2026-09-23 (session 15 — M16 Goat + Dog v2)_

## Known gaps

- `shap` has no cp313 wheel on Windows, so a bare `pip install -r requirements.txt` fails
  there; it's never imported, so skipping it is the fix (README has the command). The bigger
  version of this problem, `chromadb`/`chroma-hnswlib`, is **gone** — ml-service's whole
  suite now runs natively, no Docker.
- `springdoc-openapi` Spring-Boot-4 compatibility unverified — not added to `backend/pom.xml`
  yet. See [backend/AGENTS.md](backend/AGENTS.md).
- No `LICENSE` file yet — open decision, not yet made.
- `tests/e2e` browsers not installed yet (`npx playwright install --with-deps chromium`,
  one-time) — smoke test scaffold works, hasn't been run against a live `make up` stack yet.
- ~~Backend tests need a real Postgres~~ — no longer true, the backend is stateless.
- **Cat and Dog diagnoses return no precautions or next steps.** `DIAGNOSIS_TO_DOC_SLUG`
  has no entry for Ringworm, Mange, Scabies, Flea Allergy, Canine Distemper, Parvovirus or
  Kennel Cough, so `get_precautions()` returns empty lists for every companion-animal
  result. Found while verifying the database removal; the map is byte-identical to before,
  so it predates that work. Fixing it means writing six or seven reference documents in
  `data/veterinary-reference/`, the same hand-authored basis as the livestock ones.
- **A livestock photo submitted under Cat or Dog is not caught** by the species check, and
  no threshold fixes it: a cow photo with Dog selected has a median ratio (3.9) *below* the
  90th percentile of genuinely valid cat photos (10.4), so the distributions overlap. The
  guard covers the common mistake — a pet photo under livestock — only. A purpose-trained
  species classifier would close this; generic ImageNet cannot.
- **Image validation refuses ~7.5% of valid photos** (both gates combined), mostly extreme
  close-ups of lesions. Deliberate: a refusal is recoverable in one retry, and the
  alternative was a screenshot diagnosed as "Kennel Cough, 42%".

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
- **M11 PR merged to `main`** (issue #20) — confirmed via `git pull` before branching for
  M12.
- **M12 done, not yet merged** (issue #21, branch `feat/m12-sheep-disease-detection`,
  branched from synced `main`): Sheep added as a third species. Much lighter than M11, as
  designed — no architecture change, per that issue's own "not in scope." Confirmed via web
  research (not assumed): Foot and Mouth Disease affects sheep too (though sheep/goats often
  show little or no visible illness with FMD, unlike cattle — a real detection-risk nuance).
  More significantly: **foot rot and sheep pox are real, common sheep-specific diseases the
  current 5-disease model can't represent at all** — a bigger gap than Buffalo had, where
  the existing classes were at least a reasonable approximation. No sheep dataset found
  either (same pattern as M9/M11). Implementation: `SHEEP` added to the `Species` enum
  (one line — the M11 architecture needed nothing else) and to frontend
  `SPECIES_OPTIONS`; the non-Cow disclosure text was **strengthened** to say some diseases
  aren't representable at all, not just "not trained on this species" — the Buffalo-era
  wording would have undersold Sheep's actual gap. Spec:
  [docs/specs/M12-sheep-disease-detection.md](docs/specs/M12-sheep-disease-detection.md).
  **Validated**: backend 18/18, ml-service unaffected (36/2 skipped, no ml-service files
  touched), frontend lint + 10/10 + build all green, **plus live end-to-end verification**:
  created a Sheep animal via `POST /api/animals` in a real browser, confirmed the
  strengthened disclosure rendered, submitted FMD-indicative symptoms, and confirmed the
  diagnosis correctly escalated (`Foot and Mouth Disease`, `escalate_to_vet`) via the shared
  model.
- **M12 PR merged to `main`** (issue #21) — confirmed via `git pull` before branching for
  M13.
- **M13 done, not yet merged** (issue #22, branch `feat/m13-cat-disease-detection`, branched
  from synced `main`): Cat added as a fourth species — the real pivot in the M11–M14
  sequence. **Key judgment call: diagnosis is NOT reused from the cattle model for Cat**,
  unlike Buffalo/Sheep. Buffalo/Sheep share the livestock disease family closely enough
  (FMD, LSD) that reuse is a disclosed approximation; a cat doesn't get any of the 5 modeled
  diseases, and the symptom vocabulary (`milk_yield_drop`, `udder_swelling`, etc.) is
  nonsensical for a cat — predicting "Foot and Mouth Disease" for a cat would be actively
  wrong, not just imprecise. **Diagnosis is blocked entirely for Cat, enforced at both
  layers**: `DiagnosisService` rejects with a new `400 DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`
  (works even via a direct API call, not just hidden in the UI), and the frontend replaces
  the symptom/photo forms with an explicit "not available yet" block when Cat is selected
  (not a disabled-but-visible form). Resolved issue #22's three open questions with real
  research: (1) initial cat disease list — Feline Upper Respiratory Infection, ringworm,
  FIV — documented for future use, not wired into any model; (2) escalation-equivalent for
  companion animals — **rabies**, a legally mandatory reportable disease for cats/dogs,
  confirmed via research, now documented; (3) `docs/DISCLAIMER.md` updated with a new
  companion-animal section covering both of the above. Also found (not downloaded) real
  candidate cat-disease datasets — a Hugging Face-mirrored symptom dataset and Roboflow
  image sets — flagged as follow-up, needs the user's go-ahead before fetching. Spec:
  [docs/specs/M13-cat-disease-detection.md](docs/specs/M13-cat-disease-detection.md).
  **Validated**: backend 21/21, ml-service unaffected (36/2 skipped), frontend lint +
  11/11 + build all green, **plus live end-to-end verification**: created a Cat animal via
  `curl`, directly confirmed both the symptom and image diagnosis endpoints reject it
  cleanly, and in the real browser confirmed selecting Cat hides the symptom/photo forms
  entirely (switching back to Cow correctly restores them).
- **M13 PR merged to `main`** (issue #22) — confirmed via `git pull` before branching for M14.
- **M14 done, not yet merged** (issue #23, branch `feat/m14-dog-disease-detection`, branched
  from synced `main`): Dog added as a fifth species — the last of the five from the original
  request. **Deliberately mirrors M13's "block, don't approximate" call rather than issue
  #23's literal "source a dataset, train and wire in a dog-aware model" wording** — same
  reasoning as Cat (the cattle model's disease list/symptom vocabulary don't apply to a
  companion animal at all), confirmed explicitly with the user before starting rather than
  assumed. Resolved issue #23's research asks with real citations (AVMA, VCA, AKC): a starter
  dog disease list (canine distemper, canine parvovirus, kennel cough/CIRDC, sarcoptic/
  demodectic mange), documented for future use, not wired into any model. Rabies
  escalation-equivalent and `docs/DISCLAIMER.md`'s companion-animal framing were **not**
  re-derived — both were already written dog-inclusive by M13, confirmed by rereading the
  file rather than assumed, so `DISCLAIMER.md` needed no edit this milestone (a deliberate,
  documented decision, not an oversight). Implementation: `DOG` added to the `Species` enum
  and frontend `SPECIES_OPTIONS`; `DiagnosisIntake.jsx`/`AnimalIdentityFields.jsx` needed no
  code changes since both already gate generically on `DIAGNOSIS_SUPPORTED_SPECIES` with no
  Cat-specific hardcoding. `docs/API_CONTRACTS.md` updated (`DOG` in the species list, the
  `CAT`-only rejection paragraph extended to cover both). Found (not downloaded) the same
  Hugging Face pet-symptoms dataset M13 flagged, plus two Kaggle multi-species candidates —
  flagged as follow-up, same "ask before fetching" boundary. Spec:
  [docs/specs/M14-dog-disease-detection.md](docs/specs/M14-dog-disease-detection.md).
  **Validated**: backend 23/23 (2 new tests each in `AnimalServiceTest`/
  `DiagnosisServiceTest`, mirroring the Cat tests), ml-service unaffected (no ml-service files
  touched), frontend lint + 12/12 + build all green, **plus live end-to-end verification**:
  created a Dog animal via `curl`, confirmed both the symptom and image diagnosis endpoints
  reject it with a clean `400 DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`, confirmed a Cow diagnosis
  still succeeds normally, and in the real browser confirmed selecting Dog hides the
  symptom/photo forms entirely (switching back to Cow correctly restores them).
- **M14 PR merged to `main`** ([#30](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/pull/30)) — confirmed before branching for M9.
- **M9 done** (issue #18): the long-standing Kaggle blocker resolved itself — `kagglehub`
  downloaded the 3,244-image cattle-diseases-datasets anonymously, no account/API token
  needed after all (the earlier assumption that one was required was wrong). Trained a real
  image classifier: MobileNetV2 backbone (ImageNet-pretrained, frozen) with a fine-tuned
  linear head over cached backbone features — CPU-feasible, ~86% validation accuracy / 0.857
  macro F1 across all 3 classes (`Healthy`/`Lumpy Skin Disease`/`Foot and Mouth Disease` —
  `Mastitis`/`Bovine Respiratory Disease` still not covered, no image data exists for them).
  Replaced M8 phase 1's SHA256-hash placeholder in `predict_image_node`
  (`ml-service/app/agent/graph.py`) with a real call to the trained model, and removed the
  `image_placeholder` branch in `explain_node` — image diagnoses now go through the same
  real LLM/RAG explanation path as symptom diagnoses. New:
  `ml-service/app/models/image_model.py` (inference wrapper, same `predict()` shape as
  `symptom_model.py`), `ml-service/training/image_model_train.py` (mirrors
  `symptom_model_train.py`'s structure). Also downloaded and evaluated 3 companion-animal
  datasets this session (Hugging Face pet-symptoms, 2 Kaggle multi-species) — **not used**:
  none had enough real Dog/Cat-specific, correctly-labeled rows to train something
  trustworthy (best one had ~75 Dog / ~72 Cat rows spread across 20+ near-duplicate disease
  labels); documented as a follow-up blocker rather than shipped as a low-confidence model,
  confirmed with the user before proceeding this way. Key architectural note: unlike the
  symptom model, the real image dataset/artifact are gitignored (large, unverified
  redistribution license) so CI can't retrain or test against them — real-model image tests
  (`test_image_base64_produces_a_real_diagnosis_per_class` etc.) skip gracefully there via
  `@pytest.mark.skipif`, while a new always-runs test confirms the clean `MODEL_NOT_TRAINED`
  503 CI will actually see. Spec:
  [docs/specs/M9-cattle-image-classifier.md](docs/specs/M9-cattle-image-classifier.md).
  **Validated**: ml-service 40/2 (skipped), backend 23/23 and frontend unaffected (confirmed
  no files touched in either — species was never threaded to the image endpoint), **plus
  live end-to-end verification**: called the real `ml-service` `/agent/diagnose` endpoint and
  the real backend `POST /api/animals/{id}/diagnoses/image` multipart endpoint with one real
  photo per class, all three correctly diagnosed with correct escalation
  (Lumpy/FMD → `escalate_to_vet`, Healthy → `monitor`).
- **M9 PR merged to `main`** ([#31](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/pull/31))
  — first CI run failed (`ml-service` job: `pip install -r requirements.txt` resolved
  `torch`/`torchvision` to PyPI's default CUDA build, exhausting the runner's disk); fixed by
  pinning `torch==2.14.0+cpu`/`torchvision==0.29.0+cpu` plus a `--extra-index-url` directive
  in `requirements.txt`, verified in a disposable local venv against a plain
  `pip install -r requirements.txt` before pushing the fix — CI went green after.
- **Real Cat and Dog image models trained and wired in** (M13/M14 follow-up, branch
  `feat/m13-m14-real-cat-dog-image-models`): you asked to train all 5 species; Roboflow
  (the candidates M13 flagged) turned out to need a login/API key (confirmed by testing), so
  a fresh Kaggle search found better, anonymously-downloadable data instead —
  `nofalrafif/cat-skin-disease` (1,000 images, 4 balanced classes incl. a real Healthy class)
  and `smadive/pet-disease-images` (293 Dog images across the same 4 diseases M14 already
  researched). Also downloaded and evaluated 2 more Kaggle sets
  (`fahimsarker/ringworm-dataset-for-classification`, single-class, not independently
  useful) — documented, not used.
  - **Cat**: real, solid — 83.0% accuracy, 0.829 macro F1 across Flea Allergy/Healthy/
    Ringworm/Scabies. **This disease list replaces M13's original URI/Ringworm/FIV research**
    — no image data exists for URI or FIV; you confirmed using the real available classes and
    updating the spec, per the same "swap in real data over the original research when they
    conflict" precedent M9 itself set.
  - **Dog**: real but genuinely weak — 52.6% accuracy, 0.489 macro F1, only 0.25 F1 for
    Canine Distemper specifically (worse than random). Tried horizontal-flip augmentation
    (split before augmenting, to avoid leaking into validation) as a legitimate fix — didn't
    move the number; likely a signal problem (systemic diseases don't have Mange's strong
    visual signature), not a volume problem. **No Healthy class exists for Dog at all** in
    anything found. **Shipped anyway, loudly disclosed** — confirmed with you explicitly
    rather than silently choosing either "hide it" or "ship it quietly." The frontend shows
    the real accuracy number and the no-Healthy-class gap prominently before any photo is
    uploaded, and `docs/DISCLAIMER.md` carries the same caveat.
  - **Architecture**: species is now forwarded from backend to `ml-service` for the IMAGE
    endpoint only (never for symptoms — that stays exactly as before, no per-species symptom
    model exists). `DiagnosisService.requireDiagnosisSupported` split into
    `requireSymptomDiagnosisSupported` (unchanged) and `requireImageDiagnosisSupported` (now
    covers Cat/Dog too, via new `IMAGE_ONLY_SUPPORTED_SPECIES`). `ml-service/app/agent/graph.py`
    picks the model by species (`_IMAGE_MODEL_BY_SPECIES`), defaulting to the cattle model
    for Cow/Buffalo/Sheep/unset — unchanged behavior there, confirmed via a regression test.
    Frontend's binary "full vs. blocked" UI became 3-way (full / image-only / blocked) —
    Cat/Dog now show only the photo-upload form, no symptom checklist, with their own
    disclosure text (Cat: informational; Dog: a loud ⚠️ warning).
  - Rabies escalation remains **not implemented as code** for either species — neither
    trained model has a Rabies class, so there's nothing for an escalation rule to attach to;
    same honest "not yet" M13 already stated, unchanged by real models now existing for other
    diseases.
  - Specs updated: `docs/specs/M13-cat-disease-detection.md` and
    `M14-dog-disease-detection.md` each gained a "Follow-up" section with the real numbers.
  - **Validated**: ml-service 45/2 (skipped, including new Cat/Dog routing/escalation/
    missing-model tests — made statistically robust with random-sampled multi-image checks
    after an initial flaky single-sample version), backend 24/24 (2 rejection tests →
    2 success-and-forwards-species tests), frontend lint + 13/13 + build all green, **plus
    live end-to-end verification**: real Cat/Dog photos through the actual backend multipart
    endpoint (correct diagnoses), confirmed symptom submission still rejects for both,
    confirmed Cow regression-free, and confirmed in the real browser that Cat/Dog show the
    image-only form with the correct disclosure text (Cow's full form unaffected).
- **PR opened** ([#32](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/pull/32)), stacked on the merged M9 PR. CI passed (`frontend`/`backend`/`ml-service`) after
  fixing a duplicate `dog_image_model.pt` row in `REGISTRY.md` (the training script appends,
  doesn't replace — caught while answering "how much data is each model trained on"). Also
  added a `README.md` section on testing diagnosis manually and retraining any model from
  scratch. `mergemitra-analysis`, an org-level check unrelated to this repo's own CI, fails
  the same way it did on PR #31 — not something in scope here.
- **Multi-photo upload + species preview + visual redesign** (new branch
  `feat/multi-photo-diagnosis-ui`, stacked on the Cat/Dog branch per your explicit choice
  rather than waiting for #32 to merge first): you asked for three things —
  1. **Species preview**: a card showing the species' icon + a one-line capability summary,
     swapping instantly on selection (`SpeciesPreview.jsx`, new). Inline emoji only, matching
     the original farm-themed redesign's "no downloaded imagery" convention.
  2. **Up to 5 photos per diagnosis, with a disagreement warning**: confirmed with you this
     means comparing the 5 photos' own diagnosis results against each other (not verifying
     "is this actually a cat" — that would need a whole new species-detection model, flagged
     as out of scope, not started). `POST /api/animals/{id}/diagnoses/image` now takes 1-5
     files (`@RequestParam("images") List<MultipartFile>`, was one `image`) and returns
     `ImageDiagnosisBatchResponse { results: [...], diagnosesAgree }` — a breaking API change,
     acceptable per `docs/DECISIONS.md`'s standing local-project position (same precedent as
     M11's rename). Backend loops the existing single-image `ml-service` call once per photo —
     **no ml-service changes**. Frontend: `ImageUploadForm.jsx` reworked into a 5-slot photo
     tray (add/remove per slot); `DiagnosisResult.jsx` split into `DiagnosisResultCard` +
     `DiagnosisResultList`, the latter shows a warning banner when `diagnosesAgree === false`.
     Symptom-based diagnosis (Cow/Buffalo/Sheep) is untouched — still returns/renders a single
     result.
  3. **Visual polish**: real card styling for the species preview and photo tray, an animated
     spinner replacing the plain "⏳ Submitting…" text, entrance animation on the species
     preview and result cards. Kept the existing gradient-sky/farm background — confirmed via
     screenshot it was already good, the flatness was in the form chrome, not the backdrop.
  **Validated**: `mvn -q test` 16/16 (3 new: agree-case, disagree-case, >5-images rejection),
  `npm test` 14/14 (1 new: multi-photo disagreement banner) + build green. Live end-to-end via
  `curl`: 2 Ringworm-ish Cat photos correctly flagged `diagnosesAgree: false` when one came
  back a different diagnosis, 3 Dog Mange photos correctly flagged disagreement when one came
  back `uncertain`, 6-photo submission correctly rejected with `TOO_MANY_IMAGES`. Confirmed
  live in the browser (desktop + mobile 375px) that the species preview swaps correctly for
  all 5 species and the photo tray's 5 slots render with correct accessible labels — could
  not literally drive the file picker in the built-in browser (same tooling limitation as
  M9), covered instead by the passing Vitest suite's `user.upload()` simulation.
- **Found and fixed a real bug while explaining the app to the user**: `POST /api/animals`
  always inserted a new row, so a second diagnosis for the same real animal (same tag number)
  permanently failed with `ANIMAL_TAG_DUPLICATE` — there was no way to ever revisit an animal
  after its first diagnosis, which defeats the point of `tagNumber`/`farmId` existing at all
  (case history, per `AGENTS.md`'s stated backend responsibility). `AnimalService.create` →
  `findOrCreate`: looks up by tag first (globally unique, confirmed via
  `V1__init.sql`), reuses the existing record when `farmId`/`species` both match, still
  rejects as a real conflict if either doesn't (prevents silently overwriting an existing
  animal's history via a typo'd tag). New repository method `findByTagNumber`. Backend
  30/30 (3 new tests: reuse-on-match, reject-on-farm-mismatch, reject-on-species-mismatch).
  Live-verified: two diagnoses submitted for the same tag both landed on the same `animalId`,
  and a farm/species mismatch on a reused tag still cleanly rejects.
- **Buffalo removed; Sheep gets a real, trained PPR model** (2026-09-22, direct user request
  after asking "which species are trained well" and being told no usable buffalo/sheep
  dataset had ever been found): `BUFFALO` dropped from `Species` (backend enum) and
  `SPECIES_OPTIONS` (frontend) — two dataset searches months apart both found nothing, so
  rather than leave it a permanent "approximation," it's gone (`docs/specs/
  M11-buffalo-disease-detection.md` marked superseded, not deleted). New Flyway migration
  (`V3__remove_buffalo_species.sql`) cleans up any existing `species = 'BUFFALO'` rows.
  Sheep, meanwhile, got a real dataset this time —
  [PPR disease data from goats and sheep](https://www.kaggle.com/datasets/devothanyambo/ppr-disease-data-from-goats-and-sheep)
  (real field-collected, RT-qPCR-confirmed clinical data) — and now has its own trained
  binary PPR (Peste des Petits Ruminants) screen (`app/models/sheep_symptom_model.py`,
  80.5% CV accuracy, 78.8% macro F1), replacing the cattle-model approximation on the
  *symptom* path only (image diagnosis for Sheep is unchanged — still the cattle model, no
  sheep-specific image dataset exists). Real caveat, disclosed: the dataset's `animal`
  column is an undocumented 0/1 encoding with no way to verify which value means sheep vs.
  goat, so the model trains on the combined goat+sheep file rather than a guessed-at subset
  — full detail in `ml-service/data/sheep-symptoms/SOURCE.md`. `species` is now forwarded to
  `ml-service` on the symptom path too (previously only the image path was species-aware).
  `PPR (Peste des Petits Ruminants)` added to `REPORTABLE_DISEASES` (WOAH/OIE-notifiable,
  escalates same as FMD/LSD). Frontend: Sheep now renders its own symptom checklist
  (`symptomFields.js`'s `SHEEP_SYMPTOM_FIELDS` — 6 fields, a completely different vocabulary
  from cattle's) instead of the cattle checklist, with rewritten disclosure copy describing
  the model's real, narrow scope. Spec: `docs/specs/M12-sheep-disease-detection.md`'s
  "Follow-up" section. **Validated**: backend 29/29 (Flyway migration applies cleanly
  against real Postgres), ml-service 50/2 (skipped, RAG — same documented local blocker as
  always; 2 new routing tests + 5 new sheep-model tests), frontend lint + 13/13 + build all
  green, **plus live end-to-end verification**: ran the real backend + ml-service, created a
  real Sheep animal, submitted real PPR-positive symptoms through the actual browser form,
  got back a correctly-escalated PPR diagnosis; confirmed Buffalo is now rejected
  (`INVALID_REQUEST_BODY`, 400) and Cow's path is unaffected (regression-checked).
- **Image-mismatch/invalid-photo detection, all 4 image-diagnosable species** (2026-09-22,
  M15, same session): a photo that isn't of an animal at all (car, table, ...) now gets a
  distinct, honest `diagnosis: "invalid_image"` / `recommendedAction: "retry_upload"` instead
  of running through a disease classifier that was never trained to say "I don't recognize
  this." New `app/models/species_gate.py` — a free, pretrained (zero fine-tuning)
  torchvision ImageNet-1k classifier, gating on whether any of the top-5 predictions falls in
  the (verified, not assumed) animal-class index range 0–397. Tested against real data before
  wiring in: this repo's own cattle/cat/dog training photos all pass (3/3), two real
  Wikimedia photos (a table, a car) are both cleanly rejected — but **synthetic test images
  (solid color, noise, checkerboard) all incorrectly pass** (documented, not hidden — ~40% of
  ImageNet-1k classes are animals, so a degenerate image's top-5 has a high chance of
  including one by pure chance; fine for the real "accidental mismatched upload" problem,
  not an adversarial boundary). Deliberately does **not** verify the photo matches the
  *selected* species (confirmed scope with the user first) — that's separate, bigger,
  previously-deferred work. Also fixed a real pre-existing bug found while building this: the
  `"uncertain"` diagnosis explanation always said "not enough *symptom* information," even
  for an image submission with no symptoms involved at all. Frontend renders `invalid_image`
  with its own dedicated card style (no confidence %, no vet-triage badge — neither concept
  applies). Multi-photo batches exclude `invalid_image` from the `diagnosesAgree` comparison
  (backend). Spec: `docs/specs/M15-image-diagnosis-quality-gate.md`. **Validated**: backend
  33/33, ml-service 63/2 (skipped, RAG — same documented blocker as always; 8 new tests: 5
  for the gate directly, 3 for graph.py routing across all 4 species), frontend lint + 14/14
  all green, **plus live end-to-end verification against the real running stack**: a real
  car photo submitted through the actual backend + ml-service came back `invalid_image` /
  `retry_upload` exactly as designed; a real cat photo submitted right after came back a
  correct `Ringworm` diagnosis (regression-checked, same request path).

- **Animal identity removed entirely** (branch `refactor/remove-animal-identity`, spec
  [docs/specs/remove-animal-identity.md](docs/specs/remove-animal-identity.md)). The user
  decided tag numbers and farm IDs were no longer needed; asked which way to take it, they
  chose dropping the animal record outright over keeping a thin `id + species` one.
  - Gone: the whole `com.cattlecare.backend.animal` package (entity, repository, service,
    controller, both DTOs), `POST /api/animals`, both `/api/animals/{id}/diagnoses*` routes,
    the `animal` table, the `ANIMAL_TAG_DUPLICATE`/`ANIMAL_NOT_FOUND` error codes, the
    find-or-create-by-tag behavior, and the tag/farm form fields with their validation.
  - Kept: `Species` (moved to the `diagnosis` package — it genuinely picks which trained
    model runs), case history, the correlation ID, and every species-support rule
    (Cat/Dog symptom diagnosis still rejected; image diagnosis still allowed for all four).
  - `diagnosis_case` now carries its own `species` column instead of `animal_id`.
    `V4__remove_animal_identity.sql` backfills it **from the animal each case pointed at**
    before dropping the join, so historical cases keep their real species rather than all
    being stamped `COW` — verified on a seeded scratch database (a SHEEP case stayed SHEEP).
  - API is one call per diagnosis now (`POST /api/diagnoses`, `POST /api/diagnoses/image`
    with `species` as a form field), down from two. The frontend makes one request instead
    of two.
  - `ml-service` was not touched at all — it never knew about tags or farms. Its suite
    (63 passed, 2 skipped) was re-run to prove it.
  - Verified: `mvnw -B verify` 20/20 green against a scratch Postgres (full V1→V4 migration
    chain applies clean, and Hibernate's `ddl-auto: validate` confirms the entity matches
    the migrated schema); frontend lint clean, 12/12 tests, production build OK.

- **Both databases removed** (spec
  [docs/specs/remove-databases.md](docs/specs/remove-databases.md), decision logged in
  `docs/DECISIONS.md`). Asked whether either was needed, the answer was measured rather than
  argued: with both absent, symptom diagnosis was 6/6 correct and image diagnosis 5/5 on real
  labelled photos, but precautions/next-steps came back **empty** — including for FMD, where
  the farmer was told to escalate with no guidance.
  - **Postgres deleted entirely**: entity, repository, all four Flyway migrations, the JPA /
    Flyway / postgresql dependencies, the datasource config, the compose service and CI's
    service container. It was write-only (two saves, zero queries) yet a hard startup
    dependency — the backend would not boot without it. Now stateless; boots in 1.8s instead
    of ~10s, and `mvn verify` passes with no database anywhere.
  - **Chroma replaced by direct markdown reads**, not deleted in spirit: `app/rag/` still
    does RAG, it just reads `data/veterinary-reference/*.md`. The corpus is 10.8 KB over six
    documents that both callers addressed by exact key, so the index earned nothing.
    `retrieve()` is now an exact lookup — strictly narrower, it can't surface another
    disease's text. The precautions text is byte-identical, pinned by a golden-output test.
  - **`DiagnosisCaseResponse.id` removed** — no row, nothing to identify. `createdAt` stays;
    the correlation ID remains the tracing handle.
  - Verified by running the stack natively (Docker was down, which made the point): 6/6
    symptom scenarios correct *with* full guidance, image diagnosis byte-identical to the
    pre-change run on the same five photos, multi-photo agreement intact. Suites:
    **ml-service 79 passed / 0 skipped natively** (was 63 passed / 2 skipped, RAG file
    skipped outside Docker), backend 20/20 with no DB, frontend 23/23.
  - Pre-existing gap noticed, not introduced: cat/dog diagnoses (Ringworm, Mange, ...) have
    no reference documents, so they return no guidance. The diagnosis→document map is
    byte-identical to before, so this predates the change.

- **M16: Goat added as a real, image-only species; Dog's model retrained on a better dataset**
  (2026-09-23, branch `feat/m16-goat-species-and-dog-v2`, direct user request: "download the
  goat dataset and integrate it... if datasets for other species are available, include them
  as well"). Scope was confirmed with the user first (`AskUserQuestion`): Goat becomes a full
  new species rather than folding into Sheep, and "other species" work means replacing the
  weak Dog model specifically.
  - **Goat**: real trained image model, `app/models/goat_image_model.py` — but **binary
    only** (`Healthy`/`Unhealthy`, 80.1% accuracy, 0.800 macro F1, 927 images from
    `kartikeybartwal/dataset`, Apache 2.0). No disease-specific goat image dataset exists
    anywhere found (searched "goat disease", "goat skin disease", "goat pox" against Kaggle's
    public API) — the model can flag that a goat looks off, never name what's wrong. No goat
    symptom model either (the PPR dataset's species column is undecodable, same wall Sheep's
    model already documents). `GOAT` added to `Species` (backend) and
    `IMAGE_ONLY_SUPPORTED_SPECIES` (both services), same pattern as Cat/Dog. ImageNet has no
    dedicated goat class (verified against the model's own category list) — "ibex" used as
    the closest proxy, added to `species_gate.py`'s existing `RUMINANT` group. Spec:
    [docs/specs/M16-goat-disease-detection.md](docs/specs/M16-goat-disease-detection.md).
  - **Dog v2**: retrained on
    [Dogs Skin disease dataset](https://www.kaggle.com/datasets/yashmotiani/dogs-skin-disease-dataset)
    (CC0, 439 images) — disease list changes entirely, from the old systemic-disease list
    (Canine Distemper/Parvovirus/Kennel Cough/Mange, no Healthy class) to a skin-disease list
    (Bacterial Dermatosis/Fungal Infection/Healthy/Hypersensitivity-Allergic Dermatosis), the
    same "swap in real data over prior research" call M13 made for Cat. **Real result: 70.5%
    accuracy, 0.683 macro F1** (was 52.6%/0.489), with a genuine Healthy class for the first
    time. Measured that the v1 model's flip-augmentation trick doesn't help this dataset (69.3%
    with it vs. 70.5% without) — training script simplified to match Cat/Goat's plain pattern.
  - **A real, unplanned regression, measured and disclosed**: the species-mismatch detector's
    dog-as-cow catch rate dropped from ~80% (v1's whole-body photos) to ~30% (v2's skin
    close-ups) — close-ups don't show the face/ears/snout signal the detector needs. Judged an
    acceptable tradeoff, not silently absorbed: logged in `docs/DECISIONS.md` with the real
    numbers, and `tests/test_species_mismatch.py` now reads the retained
    `data/dog-images-v1-superseded/` folder for that specific check so the test still validates
    the detector's real capability independent of which dataset trains the current model.
  - Also fixed along the way: Cat and Dog's `REGISTRY.md` rows were de-duplicated (the training
    script appends, doesn't replace — same class of issue PR #32 hit before), and 4 new
    hand-written reference docs were added (`bacterial-dermatosis.md`, `fungal-infection.md`,
    `hypersensitivity-allergic-dermatosis.md`, `unhealthy-goat.md`) so these new diagnoses get
    real precautions/next-steps instead of silently falling into the known Cat-only gap below.
  - `docs/DISCLAIMER.md`, `docs/API_CONTRACTS.md`, `docs/ROADMAP.md`, and
    `frontend/src/features/diagnosis/species.js`'s `SPECIES_SUMMARIES` all updated to reflect
    the real new numbers and the new species.
  - **Validated**: ml-service 94/1 (skipped), backend 32/32, frontend lint + 27/27 + build all
    green, plus live end-to-end verification against the real running stack (see HANDOFF.md).

## In Progress

Nothing in progress. Every PR from this session is merged (#35 through #40), apart from the
documentation PR carrying this update.

## Not Started

- M7: Notifications (email/WhatsApp free tier)

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
