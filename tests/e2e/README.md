# End-to-end tests

Playwright tests that verify the full flow across all three services (`frontend` →
`backend` → `ml-service`) against a running `docker compose up` stack. Not unit tests —
those live inside each service's own `tests/`/`src/test/` folder.

## Setup (one-time)

```bash
cd tests/e2e
npm install
npx playwright install --with-deps chromium
```

## Run

```bash
make up          # from repo root, in another terminal — starts all 3 services
make test-e2e     # from repo root
# or directly:
cd tests/e2e && npx playwright test
```

## What's covered today

`smoke.spec.js` — confirms all three services are actually reachable together: backend and
ml-service health checks, the ml-service diagnose endpoint returns a correlation ID, and the
frontend renders. This is intentionally minimal until real features exist.

## What lands next

Once M4/M5 land, add `test_diagnose_flow.spec.js`: submit symptoms through the real UI,
assert a diagnosis renders with the expected shape, and confirm the same correlation ID
appears in all three services' logs for that request.
