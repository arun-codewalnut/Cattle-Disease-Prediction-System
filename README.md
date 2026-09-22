# Cattle Disease Prediction System (learning project)

An agentic-AI-assisted cattle disease prediction system: symptom/image intake → ML
diagnosis → LangGraph agent explanation and recommended action.

Free/open-source stack only — see [docs/DECISIONS.md](docs/DECISIONS.md) for why.

> **Not a certified veterinary tool.** This is a learning project. See
> [docs/DISCLAIMER.md](docs/DISCLAIMER.md) before relying on or extending its predictions.

## Structure

| Path | Stack | Purpose |
|---|---|---|
| [frontend/](frontend) | React 19 + Vite | Symptom/image intake UI |
| [backend/](backend) | Java 21 + Spring Boot 4 | Auth, case history, notifications, API gateway |
| [ml-service/](ml-service) | Python + FastAPI + LangGraph | ML models, agent orchestration, RAG |
| [docs/](docs) | — | Architecture, decisions, roadmap, API contracts |
| [agents/playbooks/](agents/playbooks) | — | Canonical how-to guides for agents/contributors |
| [.claude/skills/](.claude/skills) | — | Claude Code adapters over the playbooks above |
| [tests/e2e/](tests/e2e) | — | Full-stack flow tests |

Agent-context files: [AGENTS.md](AGENTS.md) (canonical), [CLAUDE.md](CLAUDE.md) (Claude Code
entry point), [STATE.md](STATE.md) (current progress), [HANDOFF.md](HANDOFF.md) (session
handoff notes). Each service has its own scoped `AGENTS.md`/`CLAUDE.md`.

## Prerequisites

| Tool | Needed for | Notes |
|---|---|---|
| [Node.js](https://nodejs.org/) 20+ | `frontend` | tested with Node 24 |
| [Java 21](https://adoptium.net/) + [Maven](https://maven.apache.org/) | `backend` | |
| [Python 3.13](https://www.python.org/) | `ml-service` | Windows: use the `py` launcher |
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | Postgres always; `ml-service` if you want RAG-grounded explanations (see below) | |
| [Ollama](https://ollama.com/download) (optional) | real LLM-generated explanations | without it, explanations use a deterministic template — the app works fully either way, see `docs/DECISIONS.md` |

**One real constraint to know up front**: `ml-service`'s RAG feature (M6) depends on
`chromadb`, which **cannot install natively on Windows + Python 3.13** — no prebuilt wheel
exists at all for its native dependency (confirmed via PyPI, not just "needs Build Tools").
This doesn't block you from running the app — it just decides *which* of the two options
below you want.

**Disk space**: budget ~2GB free if you want the real image classifiers trained locally —
`torch`/`torchvision` (CPU wheels) are ~130MB installed, and the three real photo datasets
(cattle/cat/dog) are a few hundred MB combined once downloaded. None of this is required just
to run the app — only to retrain a model yourself (see "Testing the application" below).

## Running locally

### Option A — Docker Compose (recommended: full features, including RAG)

```bash
cp backend/.env.example backend/.env
cp ml-service/.env.example ml-service/.env
cp frontend/.env.example frontend/.env
make up
```

Then, **one-time** (populates the RAG knowledge base — skip it and the app still runs
fine, just without grounded-explanation citations):
```bash
docker compose run --rm ml-service python -m app.rag.ingest
```

Open **http://localhost:5173**. (`backend` at `:8080`, `ml-service` at `:8000`.)

### Option B — native (faster iteration; RAG grounding gracefully disabled)

```bash
# ml-service
cd ml-service && .venv\Scripts\activate && uvicorn app.main:app --reload

# backend (needs Postgres reachable — see agents/playbooks/run-stack.md for the one-liner)
cd backend && mvn spring-boot:run

# frontend
cd frontend && npm run dev
```

Without `chromadb` installed, `ml-service` still diagnoses correctly — the RAG retrieval
step catches the missing dependency and degrades to `sources: []`, the same graceful
fallback used for any other retrieval failure. You only lose M6's citation feature, nothing
else breaks.

Full instructions (including how to run ml-service's RAG-dependent tests, which also need
Docker): [agents/playbooks/run-stack.md](agents/playbooks/run-stack.md) and
[ml-service/AGENTS.md](ml-service/AGENTS.md).

## Testing the application

Once all three services are up (either option above), open **http://localhost:5173**. The
intake form: pick a species, enter an animal tag number + farm ID, then submit symptoms
and/or up to 5 photos. What's actually supported differs by species — this isn't a bug if a
species behaves differently, it's how the underlying models were scoped. **Buffalo was
removed as a supported species** (no usable dataset was ever found for it — see
`docs/specs/M11-buffalo-disease-detection.md`'s superseded note):

| Species | Symptom diagnosis | Image diagnosis | Notes |
|---|---|---|---|
| Cow | ✅ real model | ✅ real model (86.1% acc) | The only species with a symptom+image model trained specifically on it |
| Sheep | ✅ real model — PPR screen only (80.5% acc) | ✅ Cow's model, as a disclosed approximation | Symptoms: a real, trained binary screen for one disease (Peste des Petits Ruminants) — not a broader disease list like Cow's. A negative result means "not PPR," not "healthy." Image: no sheep-specific dataset exists, still an approximation |
| Cat | ❌ blocked (no symptom model) | ✅ real model (83.0% acc) | Flea Allergy / Healthy / Ringworm / Scabies |
| Dog | ❌ blocked (no symptom model) | ✅ real, but weak (52.6% acc) | Canine Distemper / Canine Parvovirus / Kennel Cough / Mange — **no Healthy class**, disclosed loudly in the UI |

### Symptom-based diagnosis

Check boxes matching a real disease profile and submit. A few that reliably produce a
confident, correct diagnosis (from the training data's actual per-class symptom frequencies,
not guesses):
- Fever + Mouth lesions + Excessive salivation + Lameness → **Foot and Mouth Disease** (escalates)
- Fever + Skin nodules + Drop in milk yield → **Lumpy Skin Disease** (escalates)
- Fever + Udder swelling + Drop in milk yield → **Mastitis**
- Fever + Nasal discharge + Coughing + Labored breathing → **Bovine Respiratory Disease**
- Nothing checked → **Healthy**

Switching the species to Sheep swaps the checklist entirely (a completely different, real
model — see the table above): checking **Nasal discharge + Sores in mouth or nose** reliably
produces a confident **PPR (Peste des Petits Ruminants)** diagnosis (escalates); nothing
checked reliably produces **PPR Negative**.

### Image-based diagnosis (single or multi-photo)

Upload 1–5 JPEG/PNG photos in one submission (the photo tray shows thumbnails as you add
them). Real sample photos to test with live under
`ml-service/data/{cattle,cat,dog}-images/<class-name>/` once you've populated them (see
"Training/retraining a model" below) — e.g. `ml-service/data/cat-images/ringworm/` for a real
Ringworm photo.

- **1 photo**: a single diagnosis result, same as the old flow.
- **2–5 photos**: each photo is diagnosed independently, and results are shown together. If
  they don't all agree on the same diagnosis, the UI shows a **"diagnoses disagree"** warning
  banner above the results — this is a signal to the user to look more closely or take a
  clearer/different photo, not an error. Deliberately not a species-mismatch check (no
  species-detection model exists) — it only compares the diagnoses themselves, so it also
  fires for two photos of the same problem area showing genuinely different severity.
  Try it: upload one clearly healthy-looking photo alongside one diseased photo of the same
  species to trigger the warning; upload two photos of the same class to see it agree.
- **6th photo**: rejected with `400 TOO_MANY_IMAGES` before anything is sent to `ml-service`
  (limit is enforced in `backend`, see `DiagnosisService.MAX_IMAGES`).

### Repeat visits for the same animal (find-or-create)

Animal records are keyed by tag number and looked up (not always recreated) on every
diagnosis submission:
- Same tag number + same farm ID + same species, submitted again later (e.g. a follow-up
  visit weeks after the first) → reuses the existing animal record, new diagnosis case
  attached to its history. No error, no duplicate record.
- Same tag number but a **different** farm ID or species than what's on file → rejected with
  `409 ANIMAL_TAG_DUPLICATE` ("already exists for a different farm or species"). This is
  intentional: tag numbers are only unique within one farm+species in real life, so a
  mismatch is treated as a data-entry error, not silently overwritten or silently created as
  a second animal.

Try it: submit a diagnosis for tag `COW-001` / farm `1` / species `Cow` twice — the second
submission succeeds and reuses the animal. Then submit `COW-001` again with a different farm
ID — expect the `409`.

### Testing the API directly (skipping the UI)

Useful if you want to see the raw request/response shapes (full contract:
[docs/API_CONTRACTS.md](docs/API_CONTRACTS.md)):

```bash
# 1. Find-or-create the animal (returns "id" — reuses the record if this tag/farm/species
#    combination already exists, see "Repeat visits" above)
curl -X POST http://localhost:8080/api/animals \
  -H "Content-Type: application/json" \
  -d '{ "tagNumber": "COW-001", "farmId": 1, "species": "COW" }'

# 2. Symptom-based diagnosis against that animal id (Foot and Mouth Disease profile)
curl -X POST http://localhost:8080/api/animals/1/diagnoses \
  -H "Content-Type: application/json" \
  -d '{ "symptoms": { "fever": true, "mouthLesions": true, "excessiveSalivation": true, "lameness": true } }'

# 3. Or, multi-photo diagnosis against that same animal id (1-5 photos; response includes
#    "diagnosesAgree": true|false)
curl -X POST http://localhost:8080/api/animals/1/diagnoses/image \
  -F "images=@/path/to/photo1.jpg" -F "images=@/path/to/photo2.jpg"
```

`ml-service` can also be hit directly (bypassing `backend`, e.g. to isolate whether an issue
is in the ML layer or the gateway) at `POST http://localhost:8000/agent/diagnose` — see
`ml-service/app/api/diagnose.py` for its request/response shape.

### Error scenarios worth exercising

| Trigger | Response |
|---|---|
| More than 5 images in one submission | `400 TOO_MANY_IMAGES` |
| Existing tag number, different farm ID or species | `409 ANIMAL_TAG_DUPLICATE` |
| Symptom diagnosis requested for Cat/Dog | blocked client-side (no symptom model exists for them) |
| A model artifact isn't present locally yet | `503 MODEL_NOT_TRAINED` — see below to train it |
| Unreadable/corrupt image bytes | ml-service degrades to `diagnosis: "uncertain"` rather than erroring |

### Training/retraining a model

If a diagnosis attempt returns `503 MODEL_NOT_TRAINED`, the corresponding model artifact
(`ml-service/models/*.pkl`/`*.pt`, all gitignored) isn't present locally yet:

| Model | Train with | Needs real data first? |
|---|---|---|
| Symptom model (Cow) | `python -m training.generate_synthetic_data && python -m training.symptom_model_train` | No — synthetic, generates its own data |
| Sheep symptom model (PPR screen) | `python -m training.sheep_symptom_model_train` | Yes — see `ml-service/data/sheep-symptoms/SOURCE.md` |
| Cattle image model | `python -m training.image_model_train` | Yes — see `ml-service/data/cattle-images/SOURCE.md` |
| Cat image model | `python -m training.cat_image_model_train` | Yes — see `ml-service/data/cat-images/SOURCE.md` |
| Dog image model | `python -m training.dog_image_model_train` | Yes — see `ml-service/data/dog-images/SOURCE.md` |

Each `SOURCE.md` has the exact `kagglehub.dataset_download(...)` snippet — all four real
datasets (the three image ones plus the sheep symptom one) download anonymously, no Kaggle
account needed. Run from `ml-service/` with the venv active; each training run prints its
real accuracy/F1 and appends a row to `ml-service/models/REGISTRY.md`.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch/commit conventions and the issue/PR flow.
