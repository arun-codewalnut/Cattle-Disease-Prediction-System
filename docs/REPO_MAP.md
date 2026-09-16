# Repo Map

Navigation aid for a new session (human or agent) — where things are, where to start.

## Entry points

| Task | Start here |
|---|---|
| Understand the system | [docs/ARCHITECTURE.md](ARCHITECTURE.md) |
| Run everything locally | `make up`, or [agents/playbooks/run-stack.md](../agents/playbooks/run-stack.md) |
| Add a symptom/disease feature | [docs/specs/TEMPLATE.md](specs/TEMPLATE.md) → `ml-service/app/models/` |
| Add a UI screen | `frontend/src/` |
| Add an API endpoint (business logic) | `backend/src/main/java/com/cattlecare/backend/` |
| Add an API endpoint (ML/agent) | `ml-service/app/api/` |
| Change the DB schema | new file in `backend/src/main/resources/db/migration/` |
| Change how the agent reasons | `ml-service/app/agent/graph.py` |

## Common change paths

- **"Add a new disease model"** → `agents/playbooks/add-disease-model.md` (the full recipe)
- **"Something broke across services"** → check `X-Correlation-Id` in logs of all three
  services (see [docs/ARCHITECTURE.md](ARCHITECTURE.md#request-tracing))
- **"API contract needs to change"** → update [docs/API_CONTRACTS.md](API_CONTRACTS.md)
  first, then regenerate the OpenAPI spec, then implement

## Do-not-touch / handle-with-care

- `backend/src/main/resources/db/migration/*.sql` — never edit an existing migration that
  may have run; always add a new one.
- `docs/api/*.openapi.json` — generated, don't hand-edit.
- `.claude/hooks/*.js` — these are safety guardrails (see root `AGENTS.md`); changing them
  needs explicit user sign-off, not a routine edit.
- Anything under `ml-service/app/agent/` or the `recommended_action` field — read
  [docs/DISCLAIMER.md](DISCLAIMER.md) first, this is the safety-constrained diagnosis path.

## Tests, by service

| Service | Location | Run |
|---|---|---|
| `backend` | `src/test/java/` | `mvn -q test` |
| `ml-service` | `tests/` | `pytest` (from `ml-service/`) |
| `frontend` | `src/**/*.test.jsx` (once wired, see `frontend/AGENTS.md`) | `npm test` |
| cross-service | `tests/e2e/` | `npx playwright test` (from `tests/e2e/`) |

Full strategy: [docs/TESTING.md](TESTING.md).
