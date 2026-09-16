@../AGENTS.md

## frontend-specific conventions

- **Stack**: React 19, Vite 8, `oxlint` for linting.
- **Run**: `npm run dev` (port 5173 by default). **Build**: `npm run build`. **Lint**:
  `npm run lint`.
- **Tests**: Vitest + React Testing Library, configured in `vite.config.js`. `npm test` runs
  them. Use role-based queries (`getByRole`, `getByLabel`) like `App.test.jsx` does — not
  CSS selectors or test IDs, same rule as the Playwright e2e suite. See
  [docs/TESTING.md](../docs/TESTING.md).
- **API base URL**: read from `VITE_API_BASE_URL` (see `.env.example`) — always call the
  Java `backend`, never call `ml-service` directly from the frontend.
- **Correlation ID**: generate a UUID per user-initiated request (e.g. per diagnosis
  submission) and send it as `X-Correlation-Id` to the backend. Log it to the console on
  error so it can be matched against backend/ml-service logs.
- **Errors**: the backend returns `{ code, message, details }` on failure — handle all API
  errors through one shared client/handler that expects this shape, don't write per-call
  error parsing.
