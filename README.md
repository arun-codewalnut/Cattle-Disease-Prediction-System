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

There are two ways to run this (Option A / Option B below) and they need different things.
**Option A needs only Docker** — nothing in the table below it except Docker itself.

| Tool | Needed for | Notes |
|---|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | **Option A (all services)**; Postgres in either option; `ml-service`'s RAG feature and RAG tests | the only way to get RAG-grounded explanations — see the native-install note below |
| [GNU Make](https://www.gnu.org/software/make/) (optional) | the `make` shortcuts | not installed on Windows by default — every target is a one-line `docker compose …` you can run directly instead, see [Makefile](Makefile) |
| [Node.js](https://nodejs.org/) 20.19+ or 22.12+ | Option B `frontend` | Vite 8 rejects 20.0–20.18, 21.x and 22.0–22.11; the frontend **tests** (Vitest 5) need 22.12+. CI and `frontend/Dockerfile` both use Node 24 |
| [Java 21](https://adoptium.net/) | Option B `backend` | a system [Maven](https://maven.apache.org/) is optional — `backend/mvnw` (`mvnw.cmd` on Windows) works without one |
| [Python 3.13](https://www.python.org/) | Option B `ml-service` | Windows: use the `py` launcher. Read the native-install note below before `pip install` |
| [Ollama](https://ollama.com/download) (optional, either option) | real LLM-generated explanations | without it, explanations use a deterministic template — the app works fully either way, see `docs/DECISIONS.md` |

**You must train at least one model before the app can diagnose anything** — model
artifacts are gitignored, so a fresh clone has none and every diagnosis returns
`503 MODEL_NOT_TRAINED`. It's one command and it's a step in both options below.

**Internet access on the first *image* diagnosis**: M15's "is this even a photo of an
animal?" gate uses an off-the-shelf pretrained ImageNet MobileNetV2, and `torchvision`
downloads those weights (~14MB) the first time an image is diagnosed, caching them under
`~/.cache/torch` (image *training* pulls the same weights). Symptom-only diagnosis never
needs this.

**Native install on Windows + Python 3.13 doesn't work straight from `requirements.txt`** —
two packages have no prebuilt wheel there and need Microsoft C++ Build Tools to compile from
source: `chroma-hnswlib` (a `chromadb` dependency, and no `cp313` wheel exists for it at
all — see [ml-service/AGENTS.md](ml-service/AGENTS.md)) and `shap`. `shap` isn't imported
anywhere in the code (M1 uses XGBoost's own `pred_contribs` instead), so the practical
workaround is to install everything *except* those two — the exact command is in Option B.
Docker (Option A) has neither problem: its image installs the full file, `build-essential`
included.

**Disk space** (measured, not estimated): the `ml-service` Docker image is **~3.9GB** built,
and a native `ml-service` venv is **~1.2GB** — `torch`/`torchvision` dominate both, and
they're required for *any* install, not optional. Add a few hundred MB more if you want the
real image classifiers trained locally (the cattle/cat/dog photo datasets). Only the Cow
symptom model needs no dataset at all.

## Running locally

### Option A — Docker Compose (recommended: full features, including RAG)

**1. Create the three `.env` files.** Not optional — `docker-compose.yml` declares an
`env_file` for each service, so compose fails to start if any is missing. The checked-in
examples hold working local-dev defaults, so a plain copy is all you need:

```bash
cp backend/.env.example backend/.env
cp ml-service/.env.example ml-service/.env
cp frontend/.env.example frontend/.env
```

**2. Start the stack** (`make up` wraps `docker compose up --build`; use the right-hand
command if you don't have `make`):

```bash
make up          # or: docker compose up --build
```

**3. Train the Cow symptom model** — **required once**, otherwise every diagnosis returns
`503 MODEL_NOT_TRAINED` (see the prerequisites note). This is the one model that needs no
downloaded dataset; it generates its own synthetic training data. The container writes the
artifact to `ml-service/models/` on your machine through the bind mount, so it survives
`make down` and image rebuilds — you only do this once:

```bash
docker compose run --rm ml-service python -m training.generate_synthetic_data
docker compose run --rm ml-service python -m training.symptom_model_train
```

Every *other* model (Sheep symptoms, and the cattle/cat/dog image classifiers) needs a real
dataset downloaded first — see [Training/retraining a model](#trainingretraining-a-model)
below. Nothing forces you to train them; a species/mode you haven't trained just returns
`503` until you do.

**4. Ingest the RAG knowledge base** — optional, one-time. Skip it and the app still runs
fine, just without grounded-explanation citations:

```bash
docker compose run --rm ml-service python -m app.rag.ingest
```

**5. Verify and open.** Both health checks should answer before you use the UI:

```bash
curl http://localhost:8000/health           # ml-service  -> {"status":"ok"}
curl http://localhost:8080/actuator/health  # backend     -> {"status":"UP"}
```

Open **http://localhost:5173**. (`backend` at `:8080`, `ml-service` at `:8000`, Postgres at
`:5432` — that last one matters if you already have a local Postgres on the default port.)

Other targets: `make up-d` (background), `make logs`, `make ps`, `make down` (stop and
remove), `make test-e2e`. Each maps to one `docker compose` command in the [Makefile](Makefile).

### Option B — native (faster iteration; RAG grounding gracefully disabled)

One-time setup per service:

```bash
# ml-service
cd ml-service
py -m venv .venv                           # macOS/Linux: python3 -m venv .venv
.venv\Scripts\activate                     # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt            # Windows: see the note right below first
python -m training.generate_synthetic_data # required once — trains the Cow symptom
python -m training.symptom_model_train     #   model, no dataset download needed

# frontend
cd frontend && npm install
```

On **Windows + Python 3.13**, that `pip install` needs
[Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
installed first, because `shap` and `chroma-hnswlib` have to compile from source there. If
you'd rather not do that system install, drop those two and install the rest — the app runs
fine without them (`shap` is never imported; `chromadb` only affects RAG citations):

```powershell
Get-Content requirements.txt | Where-Object { $_ -notmatch '^(shap|chromadb)' } |
  Set-Content -Encoding utf8 requirements-local.txt
pip install -r requirements-local.txt
```

```bash
# macOS/Linux equivalent (not normally needed — the full install works there)
grep -vE '^(shap|chromadb)' requirements.txt > requirements-local.txt
pip install -r requirements-local.txt
```

`backend` needs no setup step beyond a reachable Postgres, but it does need one running:

```bash
docker run -d --name cattlecare-db -e POSTGRES_DB=cattlecare -e POSTGRES_USER=cattlecare \
  -e POSTGRES_PASSWORD=cattlecare -p 5432:5432 postgres:16-alpine
```

Then run each service in its own terminal:

```bash
cd ml-service && .venv\Scripts\activate && uvicorn app.main:app --reload   # :8000
cd backend && ./mvnw spring-boot:run                                       # :8080  (mvnw.cmd on Windows)
cd frontend && npm run dev                                                 # :5173
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
intake form: pick a species, then submit symptoms and/or up to 5 photos. There's nothing
else to fill in — animal tag numbers and farm IDs were removed (see
[docs/specs/remove-animal-identity.md](docs/specs/remove-animal-identity.md)); species is the
only field the diagnosis actually needs, because it selects which trained model runs. What's actually supported differs by species — this isn't a bug if a
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

### Testing the API directly (skipping the UI)

Useful if you want to see the raw request/response shapes (full contract:
[docs/API_CONTRACTS.md](docs/API_CONTRACTS.md)):

```bash
# Symptom-based diagnosis (Foot and Mouth Disease profile). One call — species is required
# and has no default, since it picks which trained model runs.
curl -X POST http://localhost:8080/api/diagnoses \
  -H "Content-Type: application/json" \
  -d '{ "species": "COW", "symptoms": { "fever": true, "mouthLesions": true, "excessiveSalivation": true, "lameness": true } }'

# Or, multi-photo diagnosis (1-5 photos; response includes "diagnosesAgree": true|false).
# species travels as a form field here because the request is multipart.
curl -X POST http://localhost:8080/api/diagnoses/image \
  -F "species=COW" -F "images=@/path/to/photo1.jpg" -F "images=@/path/to/photo2.jpg"
```

`ml-service` can also be hit directly (bypassing `backend`, e.g. to isolate whether an issue
is in the ML layer or the gateway) at `POST http://localhost:8000/agent/diagnose` — see
`ml-service/app/api/diagnose.py` for its request/response shape.

### Error scenarios worth exercising

| Trigger | Response |
|---|---|
| More than 5 images in one submission | `400 TOO_MANY_IMAGES` |
| Missing `species` in the request | `400 VALIDATION_FAILED` — never defaulted, since it picks the model |
| Unrecognized `species` value | `400 INVALID_REQUEST_BODY` |
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
account needed. `kagglehub` isn't in `requirements.txt`; `pip install kagglehub` when you
want one of these datasets.

Run the commands above from `ml-service/` with the venv active (Option B), or prefix them
with `docker compose run --rm ml-service` if you're on the Docker path (Option A) and have
no local venv — `docker-compose.yml` bind-mounts `./ml-service` into the container, so the
artifact lands in `ml-service/models/` on your machine either way. Each training run prints
its real accuracy/F1 and appends a row to `ml-service/models/REGISTRY.md`.

## Running the automated tests

These are the same commands CI runs ([.github/workflows/ci.yml](.github/workflows/ci.yml)).
Strategy and per-service conventions: [docs/TESTING.md](docs/TESTING.md).

| Suite | Command | Also needs |
|---|---|---|
| `frontend` (Vitest) | `cd frontend && npm ci && npm test` | Node 22.12+ — Vitest 5 refuses to run on older versions even though Vite itself allows 20.19+ |
| `backend` (JUnit) | `cd backend && ./mvnw -B verify` | a reachable Postgres — the tests boot the real Spring context against `localhost:5432` (`cattlecare`/`cattlecare`/`cattlecare`). `make up`, or the `docker run` one-liner in Option B, gives you one |
| `ml-service` — full suite | `docker build -t ml-service-test ./ml-service` then run `pytest` in it — exact commands in [ml-service/AGENTS.md](ml-service/AGENTS.md) | Docker. This is the only way to exercise the RAG tests on Windows |
| `ml-service` — native subset | `cd ml-service && pytest` | the venv. Without `chromadb` the RAG tests skip themselves cleanly (`importorskip`) rather than failing — a green run here is *not* full coverage |
| e2e (Playwright) | `make test-e2e` | all three services running, plus one-time `cd tests/e2e && npm install && npx playwright install --with-deps chromium`. The smoke test posts a real symptom diagnosis, so the Cow symptom model must be trained first |

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch/commit conventions and the issue/PR flow.
