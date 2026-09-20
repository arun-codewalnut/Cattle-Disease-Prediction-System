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

## Testing diagnosis manually

Once all three services are up (either option above), open **http://localhost:5173**, create
an animal (tag number + farm ID + species), and submit either symptoms or a photo. What's
actually supported differs by species — this isn't a bug if a species behaves differently,
it's how the underlying models were scoped:

| Species | Symptom diagnosis | Image diagnosis | Notes |
|---|---|---|---|
| Cow | ✅ real model | ✅ real model (86.1% acc) | The only species with a symptom+image model trained specifically on it |
| Buffalo, Sheep | ✅ Cow's model, as a disclosed approximation | ✅ Cow's model, as a disclosed approximation | No buffalo/sheep-specific dataset exists (searched, none found) — UI shows this |
| Cat | ❌ blocked (no symptom model) | ✅ real model (83.0% acc) | Flea Allergy / Healthy / Ringworm / Scabies |
| Dog | ❌ blocked (no symptom model) | ✅ real, but weak (52.6% acc) | Canine Distemper / Canine Parvovirus / Kennel Cough / Mange — **no Healthy class**, disclosed loudly in the UI |

**Symptom-based**: check boxes matching a real disease profile and submit. A few that reliably
produce a confident, correct diagnosis (from the training data's actual per-class symptom
frequencies, not guesses):
- Fever + Mouth lesions + Excessive salivation + Lameness → **Foot and Mouth Disease** (escalates)
- Fever + Skin nodules + Drop in milk yield → **Lumpy Skin Disease** (escalates)
- Fever + Udder swelling + Drop in milk yield → **Mastitis**
- Fever + Nasal discharge + Coughing + Labored breathing → **Bovine Respiratory Disease**
- Nothing checked → **Healthy**

**Image-based**: upload a JPEG/PNG. Real sample photos to test with live under
`ml-service/data/{cattle,cat,dog}-images/<class-name>/` once you've populated them (see
below) — e.g. `ml-service/data/cat-images/ringworm/` for a real Ringworm photo.

**If a diagnosis attempt returns `503 MODEL_NOT_TRAINED`**: the corresponding model artifact
(`ml-service/models/*.pkl`/`*.pt`, all gitignored) isn't present locally yet. Train it:

| Model | Train with | Needs real data first? |
|---|---|---|
| Symptom model | `python -m training.generate_synthetic_data && python -m training.symptom_model_train` | No — synthetic, generates its own data |
| Cattle image model | `python -m training.image_model_train` | Yes — see `ml-service/data/cattle-images/SOURCE.md` |
| Cat image model | `python -m training.cat_image_model_train` | Yes — see `ml-service/data/cat-images/SOURCE.md` |
| Dog image model | `python -m training.dog_image_model_train` | Yes — see `ml-service/data/dog-images/SOURCE.md` |

Each `SOURCE.md` has the exact `kagglehub.dataset_download(...)` snippet and which subfolders
to copy where — all three image datasets download anonymously (no Kaggle account needed).
Run from `ml-service/` with the venv active; each training run prints its real accuracy/F1 and
appends a row to `ml-service/models/REGISTRY.md`.

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch/commit conventions and the issue/PR flow.
