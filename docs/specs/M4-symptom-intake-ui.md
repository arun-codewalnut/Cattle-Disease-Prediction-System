# Spec: Symptom intake UI

**Milestone**: M4
**Status**: partly superseded — identity fields removed from the form (2026-09-22)

> **Partly superseded.** The "Cattle Tag Number" and "Farm ID" inputs this spec specified
> were removed from the intake form, along with their client-side validation and the
> two-call submit flow (create animal, then diagnose). The form now collects a species and
> symptoms/photos only, and submits in one call. Everything else here — the symptom
> checklist, the result rendering, the shared error path — still stands. Kept as-is per this
> repo's convention of not editing history — see
> [remove-animal-identity.md](remove-animal-identity.md).

## Actor + goal

A farmer/vet fills in a cattle tag number and symptoms in the browser, submits, and sees
the diagnosis (likely disease, confidence, explanation, recommended action) without ever
touching the API directly.

## Boundaries & failure states

- The form covers exactly the 11 symptom fields the M1 model uses (`fever`,
  `appetite_loss`, `nasal_discharge`, `milk_yield_drop`, `mouth_lesions`, `lameness`,
  `excessive_salivation`, `skin_nodules`, `udder_swelling`, `coughing`,
  `labored_breathing`) — checkboxes, defaulting unchecked. An unchecked box means "no" (an
  explicit `false`), not "unknown" — every field always has a value on submit. Tri-state
  (yes/no/unknown) inputs are a possible future improvement, not this milestone.
- Every submission generates a fresh `X-Correlation-Id` (`crypto.randomUUID()`) sent on
  every backend call for that submission.
- Every API error (from either backend call below) is handled through one shared path that
  expects `{code, message, details}` and renders `message` — no per-call bespoke error
  handling.
- The result is always presented as a likelihood, never a certainty: "Likely: X (82%
  confidence)", not "Diagnosis: X". `recommendedAction: "escalate_to_vet"` renders with
  visibly higher urgency than `consult_vet`/`monitor` — see
  [docs/DISCLAIMER.md](../DISCLAIMER.md).

## Examples

**Form fields**: Cattle Tag Number (text), Farm ID (number), 11 symptom checkboxes, Submit
button.

**On submit**: calls `POST /api/cattle` (creates the cattle record), then
`POST /api/cattle/{id}/diagnoses` (submits symptoms) — see result display:
```
Likely: Foot and Mouth Disease (81% confidence)
Predicted Foot and Mouth Disease with 81% confidence, based primarily on: mouth_lesions, excessive_salivation, fever.
Recommended action: Escalate to vet (urgent styling)
```

**Edge case — duplicate tag number**: `POST /api/cattle` returns `409
CATTLE_TAG_DUPLICATE` → form shows that message inline, submission not retried
automatically, symptoms are not submitted (no orphaned diagnosis call for a cattle record
that was never created).

## Not in scope

- A cattle lookup/reuse flow (e.g. "look up my existing cattle by tag") — the backend has
  no `GET /api/cattle?tagNumber=` endpoint yet, and adding one is out of scope for a
  frontend milestone. Each submission creates a new cattle record; resubmitting the same
  tag number will hit `CATTLE_TAG_DUPLICATE` (see edge case above) — a real, known
  limitation, not silently hidden.
- Auth/user accounts (no milestone covers this yet).
- Diagnosis history / listing past cases (no `GET` endpoint for that exists yet either).
- Image upload (separate, later milestone).

## Acceptance criteria

- [x] Form renders all 11 symptom checkboxes plus tag number + farm ID fields.
- [x] Submit generates a correlation ID and calls `POST /api/cattle` then
      `POST /api/cattle/{id}/diagnoses` in sequence, using `VITE_API_BASE_URL`.
- [x] Successful result displays diagnosis, confidence (as a percentage), explanation, and
      `recommendedAction` with urgency-appropriate styling — never phrased as a certainty.
- [x] All API errors (both calls) render via one shared error-handling path expecting
      `{code, message, details}`.
- [x] A failed cattle-creation call does not attempt the diagnosis call.
- [x] Real Vitest + React Testing Library component tests (replacing the placeholder
      `App.test.jsx` counter test) covering: successful submission end to end (both API
      calls mocked), cattle-creation failure (diagnosis call never made), and
      diagnosis-call failure after successful cattle creation. (3/3 passing.)

## Discovered during implementation (two real integration bugs, both fixed)

Unit tests with mocked `fetch` couldn't catch these — found only by actually running all
three services together and submitting the form in a real browser, per the project's UI
testing convention.

1. **CORS was never configured on `backend`.** Every browser call from `frontend`
   (`localhost:5173`) to `backend` (`localhost:8080`) was blocked outright — different
   origins, no `Access-Control-Allow-Origin` header. Fixed: `backend/.../config/WebConfig.java`
   (new), a `WebMvcConfigurer` allowing `cors.allowed-origins` (defaults to
   `http://localhost:5173`) on `/api/**`.
2. **`MlServiceClient` → `ml-service` calls failed with "Invalid HTTP request received."**
   The JDK's `HttpClient` (which `RestClient` uses by default) attempts an `Upgrade: h2c`
   HTTP/2-cleartext upgrade that uvicorn's HTTP/1.1-only server rejects outright. Fixed:
   `MlServiceClient` now builds its `HttpClient` with `.version(HttpClient.Version.HTTP_1_1)`
   explicitly. See `docs/DECISIONS.md` for both.

## Agent mirror-back

**Intent**: a single-page form-to-result flow. No routing library, no global state
library — `useState` in one feature component is enough for this scope.

**Inputs/outputs**: form inputs (tag number, farm ID, 11 booleans) → two sequential backend
calls → rendered result or error.

**Assumptions flagged before coding**:
1. **The original issue didn't account for `cattleId` being required** — it was written
   before M3's actual API shape existed. Reconciled by adding tag number/farm ID fields and
   a create-then-diagnose flow, documented above rather than silently expanding scope
   further (e.g. no cattle-management screen).
2. Checkboxes always submit an explicit boolean (never `null`/missing) — the "uncertain
   when no evidence provided" behavior from M1/M2 is real but not reachable through this
   particular UI unless every box is left unchecked (which submits all-`false`, a
   legitimate "no symptoms observed" case, not "unknown" — a subtly different meaning, but
   the closest a checkbox form can represent without tri-state inputs).
3. No new npm dependency for API mocking in tests — stub the global `fetch` directly
   (`vi.stubGlobal`), consistent with keeping the dependency footprint minimal.
