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

## Running locally

```bash
cp backend/.env.example backend/.env
cp ml-service/.env.example ml-service/.env
cp frontend/.env.example frontend/.env
make up
```

Then: frontend at `http://localhost:5173`, backend at `http://localhost:8080`, ml-service at
`http://localhost:8000`.

Full instructions: [agents/playbooks/run-stack.md](agents/playbooks/run-stack.md).

## Known setup gap

`shap` and `chromadb` (native extensions) don't have prebuilt Windows wheels for Python
3.13 yet — running `ml-service` natively on Windows (outside Docker) needs
[Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
installed first. Running via `make up` (Docker) avoids this — see
[ml-service/AGENTS.md](ml-service/AGENTS.md).

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for branch/commit conventions and the issue/PR flow.
