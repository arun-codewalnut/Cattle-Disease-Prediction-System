# Testing Strategy

Test pyramid across three services — most coverage at the fast/cheap layers, thinnest at
the slow/expensive one.

```
        /\
       /e2e\        few — critical user journeys only (tests/e2e, Playwright)
      /------\
     /integr. \     some — service contracts (e.g. backend <-> ml-service)
    /----------\
   /    unit    \   most — fast, isolated logic (JUnit / pytest / Vitest)
  /--------------\
```

| Layer | Tool | Location | Scope |
|---|---|---|---|
| Unit — backend | JUnit 5 | `backend/src/test/java/` | Business logic, validators, mappers |
| Unit — ml-service | pytest | `ml-service/tests/` | Model wrappers, agent routing logic, error shapes |
| Unit — frontend | Vitest + React Testing Library | `frontend/src/**/*.test.jsx` | Components, hooks |
| Integration | pytest / JUnit (`@SpringBootTest`) | within each service's test dir | Real DB (Testcontainers) or real HTTP call between two services |
| E2E | Playwright | `tests/e2e/` | Full flow: submit symptoms in the UI → diagnosis returned, across all three running services |

## Rules (from the agentic-testing playbook, applied here)

- **Test behavior, not implementation.** A symptom-intake test checks the diagnosis that
  comes back, not that a specific internal function was called.
- **Role-based locators in Playwright** (`getByRole`, `getByLabel`), never brittle CSS/XPath
  selectors — this is the single biggest flakiness fix.
- **No fixed sleeps.** Use Playwright's auto-waiting assertions; a test that needs
  `sleep(2)` is a test with a race condition.
- **Every test independent** — no test may depend on another having run first, so the suite
  can run in parallel.
- **Mock only flaky boundaries** (e.g. a future third-party notification API), never mock
  the thing actually under test.
- **A green suite must mean something.** If you can't articulate what regression a test
  would catch, it's not pulling its weight — rewrite or drop it.

## Current status

- `backend`: default JUnit scaffold only (`BackendApplicationTests.java`) — grows with M3.
- `ml-service`: `tests/test_health.py` covers `/health` and the stub `/agent/diagnose` —
  real coverage lands with M1/M2 per [docs/specs/M1-baseline-symptom-model.md](specs/M1-baseline-symptom-model.md).
- `frontend`: Vitest configured (see `frontend/AGENTS.md`), no component tests yet — none
  exist to test until M4 builds the UI.
- `tests/e2e`: Playwright configured, one real smoke test (`smoke.spec.js`) that checks all
  three services' health endpoints respond — this already works today, run it after `make up`.
