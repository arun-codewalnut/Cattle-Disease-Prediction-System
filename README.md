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

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch/commit conventions and the issue/PR flow.
