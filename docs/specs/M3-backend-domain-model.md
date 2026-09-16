# Spec: Backend domain model, persistence, and case history

**Milestone**: M3
**Status**: done

## Actor + goal

A caller (later: `frontend`; for now, direct HTTP/tests) registers a cattle record, then
submits symptoms for that animal via the backend. The backend calls `ml-service`, persists
the resulting diagnosis case, and returns it — giving every diagnosis a durable history
tied to a specific animal.

## Boundaries & failure states

- Submitting symptoms for a `cattleId` that doesn't exist returns a structured `ApiError`
  (`code: "CATTLE_NOT_FOUND"`, `404`), not a raw exception.
- If `ml-service` is unreachable or errors, the backend returns a structured `ApiError`
  (`code: "ML_SERVICE_UNAVAILABLE"` for connection failure, `code: "ML_SERVICE_ERROR"` for
  an error response) — never a bare 500, and the failed attempt is **not** persisted as a
  diagnosis case (don't record a case that never actually got a diagnosis).
- The incoming (or generated) `X-Correlation-Id` is forwarded to `ml-service` on the
  outgoing call and stored on the persisted `DiagnosisCase` row — this is how one user
  request stays traceable across both services' logs *and* the stored history.
- `tag_number` is unique (per the existing migration) — creating a cattle record with a
  duplicate tag returns a structured error, not a raw constraint-violation stack trace.

## Examples

**Create cattle** — `POST /api/cattle`
```json
{"tagNumber": "COW-001", "farmId": 42}
```
→ `201`, `{"id": 1, "tagNumber": "COW-001", "farmId": 42, "createdAt": "..."}`

**Submit symptoms** — `POST /api/cattle/1/diagnoses`
```json
{"symptoms": {"fever": true, "mouth_lesions": true, "excessive_salivation": true}}
```
→ `201`:
```json
{
  "id": 7,
  "cattleId": 1,
  "diagnosis": "Foot and Mouth Disease",
  "confidence": 0.81,
  "explanation": "...",
  "recommendedAction": "escalate_to_vet",
  "createdAt": "..."
}
```

**Edge case — unknown cattle**: `POST /api/cattle/999/diagnoses` → `404`,
`{"code": "CATTLE_NOT_FOUND", "message": "...", "details": null}`.

## Not in scope

- Auth/user accounts (a later milestone — no `AGENTS.md`/`ROADMAP.md` milestone covers this
  yet; flag if it turns out to block M4).
- Frontend UI (M4).
- No new Flyway migration needed — `V1__init.sql` already defines `cattle` and
  `diagnosis_case` with exactly the columns this milestone needs.

## Acceptance criteria

- [x] `Cattle` and `DiagnosisCase` JPA entities matching `V1__init.sql` exactly (including
      `symptoms` as JSONB via Hibernate's native `@JdbcTypeCode(SqlTypes.JSON)` — no extra
      dependency needed).
- [x] Repository + service layer — controllers contain no business logic, only
      request/response mapping.
- [x] `MlServiceClient` wraps the outgoing call to `ml-service`, forwards
      `X-Correlation-Id`, and translates connection/response failures into the specific
      `ApiException` cases above (not a generic 500).
- [x] `POST /api/cattle` and `POST /api/cattle/{cattleId}/diagnoses` implemented per the
      examples above. (Also added `CATTLE_TAG_DUPLICATE`, 409, for a duplicate tag number —
      follows from the boundary rule above, not separately called out in acceptance criteria
      originally.)
- [x] Errors use the shared `ApiError` shape via `GlobalExceptionHandler` — new
      `ApiException` (code + HTTP status carrying) with a specific handler.
- [x] JUnit tests for the service layer (Mockito-mocked repository + `MlServiceClient` —
      fast, no real DB/network needed) covering: successful diagnosis persisted, unknown
      cattle → `CATTLE_NOT_FOUND`, `ml-service` unreachable → `ML_SERVICE_UNAVAILABLE`,
      `ml-service` error response → `ML_SERVICE_ERROR`. (8 new tests, all passing.)
- [x] Existing `BackendApplicationTests.contextLoads` still passes (needs Postgres, per
      `backend/AGENTS.md`). 9/9 backend tests passing.

## Agent mirror-back

**Intent**: give the backend real persistence and a real integration point with
`ml-service`, following the existing migration's schema exactly (no new migration needed).
Feature-organized packages (`cattle/`, `diagnosis/`, `client/`) rather than layer-organized
(`repository/`, `service/`, `controller/` top-level) — keeps each feature's files together.

**Inputs/outputs**: `POST /api/cattle` (create), `POST /api/cattle/{id}/diagnoses` (submit
symptoms, get a diagnosis back, persisted). Neither existed before this milestone.

**Assumptions flagged before coding**:
1. **M3 depends on M2 at the runtime/integration level, not the code level.** Java backend
   code doesn't import ml-service's Python files — the two services are decoupled by the
   REST boundary. So M3 can be implemented and unit-tested (with `MlServiceClient` mocked)
   independently of whether M2 has reached `main` yet. Real end-to-end testing against a
   live `ml-service` is a `make up` / manual verification concern, not this milestone's
   automated test suite.
2. Correlation ID is read from `MDC.get(CorrelationIdFilter.MDC_KEY)` inside
   `MlServiceClient` (already populated by the existing filter for the request's duration)
   rather than re-threading it through every method signature.
3. A failed `ml-service` call is not persisted as a `DiagnosisCase` — only successful
   diagnoses get a history row. This wasn't explicit in the issue but follows naturally from
   "don't record a case that never actually got a diagnosis."
4. **`explanation` is not persisted** — `V1__init.sql` has no column for it, and adding one
   is out of scope (no new migration needed). `DiagnosisCaseResponse` carries it through on
   the initial response only, sourced live from `ml-service`. A future `GET` history
   endpoint would return stored diagnosis/confidence/action but not the original
   explanation text — worth knowing if that milestone lands later.
5. **Discovered during implementation**: `RestClient.Builder` isn't auto-configured as a
   Spring bean in this Spring Boot 4 setup (missing a dedicated starter module — see
   `docs/DECISIONS.md`). `MlServiceClient` calls the static `RestClient.builder()` factory
   directly instead of injecting a builder bean, sidestepping the question of which starter
   to add.
