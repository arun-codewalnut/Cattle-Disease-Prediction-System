# Spec: Merge the Java backend into ml-service (remove Java + Spring Boot)

**Milestone**: stretch (post-M16 refactor)
**Status**: done

## Actor + goal

A farmer or vet uses the web app exactly as before: pick a species, submit symptoms or
1-5 photos, get a diagnosis card. Nothing they can see changes.

A developer runs and deploys **two** services instead of three: `frontend` (React) and
`ml-service` (Python). The Java `backend` (Spring Boot, about 600 lines) was a stateless
gateway: it validated the request, called `ml-service`'s `POST /agent/diagnose` over HTTP, and
reshaped the answer for the frontend. That gateway moves into `ml-service` as two new
endpoints that call the agent **in-process**, and the Java service, its build (Maven), its CI
job and every Java/Spring reference are deleted.

Why: one server language, one less service to build, deploy and pay for, and no
service-to-service networking (the Railway private-network problems — wrong hostname, IPv4 vs
IPv6, wrong port — disappear because there's no second hop).

## Boundaries & failure states

The public API the frontend calls is unchanged — same paths, status codes, field names and
error codes as the Java backend, so `frontend/` only changes its default base URL
(`http://localhost:8080` → `http://localhost:8000`).

### `POST /api/diagnoses` — symptom diagnosis (JSON)

Request: `{"species": "COW", "symptoms": {"fever": true, ...}}`. Unknown extra fields are
ignored.

| Condition | Status | `code` | `details` |
|---|---|---|---|
| Success | 201 | — | — |
| Body isn't valid JSON, isn't a JSON object, isn't `application/json`, or is empty | 400 | `INVALID_REQUEST_BODY` | `null` |
| `species` is not one of `COW`/`SHEEP`/`CAT`/`DOG`/`GOAT` (exact, case-sensitive) or not a string | 400 | `INVALID_REQUEST_BODY` | `null` |
| `symptoms` present but not a JSON object | 400 | `INVALID_REQUEST_BODY` | `null` |
| `species` and/or `symptoms` missing or `null` | 400 | `VALIDATION_FAILED` | `{"<field>": "must not be null", ...}` — every missing field |
| Species is `CAT`/`DOG`/`GOAT` (no symptom model) | 400 | `DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES` | `null` |

Type errors are checked before missing fields (Jackson deserialization ran before `@Valid`
in Spring), so an invalid species plus a missing `symptoms` is `INVALID_REQUEST_BODY`.

### `POST /api/diagnoses/image` — photo diagnosis (multipart)

Form fields: `species` (text) and `images` (1-5 files). Checked in this order:

| Condition | Status | `code` |
|---|---|---|
| Content-Type isn't `multipart/form-data` | 400 | `IMAGE_REQUIRED` |
| Request larger than 5 photos x 5MB (+1MB overhead) | 400 | `IMAGE_TOO_LARGE` |
| `species` missing or blank | 400 | `VALIDATION_FAILED`, details `{"species": "must not be null"}` |
| `species` not a valid value (surrounding whitespace is trimmed, as Spring did) | 400 | `INVALID_REQUEST_BODY` |
| No `images` file parts | 400 | `IMAGE_REQUIRED` |
| More than 5 images | 400 | `TOO_MANY_IMAGES` |
| Any image empty (0 bytes) | 400 | `IMAGE_REQUIRED` |
| Any image not `image/jpeg` / `image/png` (by the part's Content-Type) | 400 | `UNSUPPORTED_IMAGE_TYPE` |
| Any image over 5MB | 400 | `IMAGE_TOO_LARGE` |
| Species not image-diagnosable (all 5 are, so unreachable today) | 400 | `DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES` |
| Success | 201 | — |

All validation happens before any model runs. Photos are never written to disk.

### Both endpoints

- **Errors raised by the agent** (e.g. `MODEL_NOT_TRAINED`, 503) now reach the caller with
  their own code. Previously the Java backend wrapped them as `ML_SERVICE_ERROR` (502) with a
  message containing the raw upstream response; `ML_SERVICE_UNAVAILABLE` (503) could only
  happen when the network hop failed, and there is no hop any more. Both codes are retired.
- Any other unexpected exception: 500 `INTERNAL_ERROR`.
- An unknown path anywhere in ml-service: 404 `NOT_FOUND` in the standard error shape.
- `X-Correlation-Id`: read from the request or generated, echoed on the response (existing
  ml-service middleware), and logged with each diagnosis request.
- CORS: origins from `CORS_ALLOWED_ORIGINS` (comma-separated, default
  `http://localhost:5173`), methods GET/POST/PUT/DELETE/OPTIONS, any request header — same as
  the Java `WebConfig`.
- Inference runs in a worker thread (`run_in_threadpool`) so a slow model call doesn't block
  other requests.

### Existing ml-service endpoints

`POST /agent/diagnose` and `GET /health` are unchanged (FastAPI's default 422 still applies to
`/agent/diagnose`; the 400 mapping above applies only under `/api/`). The Spring-only
`GET /actuator/health` (`{"status":"UP"}`) is gone — `GET /health` (`{"status":"ok"}`) is the
single health check.

## Examples

Symptom diagnosis:

```http
POST /api/diagnoses
{"species": "COW", "symptoms": {"fever": true, "mouth_lesions": true, "excessive_salivation": true, "lameness": true}}
```

```json
201
{
  "species": "COW",
  "diagnosis": "Foot and Mouth Disease",
  "confidence": 0.93,
  "explanation": "...",
  "recommendedAction": "escalate_to_vet",
  "precautions": ["..."],
  "nextSteps": ["..."],
  "createdAt": "2026-09-27T10:15:30.123456Z"
}
```

`sources` from the agent is not included, exactly as the Java response didn't include it.

Photo diagnosis (3 photos, one of which isn't an animal):

```json
201
{
  "results": [
    {"species": "COW", "diagnosis": "Lumpy Skin Disease", "...": "..."},
    {"species": "COW", "diagnosis": "Lumpy Skin Disease", "...": "..."},
    {"species": "COW", "diagnosis": "invalid_image", "recommendedAction": "retry_upload", "...": "..."}
  ],
  "diagnosesAgree": true
}
```

`diagnosesAgree` ignores `invalid_image` and `species_mismatch` results; one photo always
agrees with itself.

Edge case — symptom diagnosis for a cat:

```json
400
{"code": "DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES", "message": "Symptom-based diagnosis isn't available for species CAT.", "details": null}
```

## Not in scope

- Any change to diagnosis logic, models, the agent graph, RAG, or the frontend UI.
- Authentication, rate limiting, persistence — the gateway stays stateless and open, as it
  was.
- Rewriting historical specs in `docs/specs/` — they describe what was true when written.
  Current-state docs (README, ARCHITECTURE, API_CONTRACTS, REPO_MAP, TESTING, AGENTS files,
  playbooks, STATE, HANDOFF) are updated; `docs/DECISIONS.md` gets a new entry superseding the
  polyglot-split decision rather than editing it.
- Deleting the Railway `java` service — that's a dashboard action for the owner after merge.

## Deliberate differences from the Java backend

1. `ML_SERVICE_ERROR` / `ML_SERVICE_UNAVAILABLE` are retired; agent errors surface with their
   own code (see above). The frontend has one generic error path keyed on `message`, so it
   displays these without change — and the message is now readable instead of a nested JSON
   string.
2. Total upload size: Spring capped the **whole request** at 5MB, which rejected even two
   ordinary 3MB phone photos despite the UI allowing five. The per-photo 5MB limit is kept;
   the request cap is now 5 x 5MB (+1MB overhead).
3. A non-JSON body on `POST /api/diagnoses` returns `INVALID_REQUEST_BODY`; Spring's shared
   handler returned the unrelated `IMAGE_REQUIRED` there.
4. `GET /actuator/health` is removed; use `GET /health`.

## Acceptance criteria (must be checkable)

- [x] `backend/` is deleted; no tracked file outside `docs/specs/` and `docs/DECISIONS.md`'s
      historical entries references Spring, Maven, `mvn`, Java or port 8080 as current.
- [x] `POST /api/diagnoses` and `POST /api/diagnoses/image` exist in ml-service with the status
      codes, field names and error codes in the tables above.
- [x] Every behaviour covered by the Java `DiagnosisServiceTest` and `DiagnosisControllerTest`
      has an equivalent pytest in `ml-service/tests/`, and they pass.
- [x] The existing ml-service suite still passes unchanged.
- [x] Frontend tests pass; the frontend's default API base URL is `http://localhost:8000`.
- [x] `docker compose up` runs two services, and a symptom and a photo diagnosis through the
      frontend's API path (`/api/...` on :8000, with a `http://localhost:5173` Origin) succeed.
- [x] CI has no Java job; the pre-commit hook has no Maven step.
- [x] `docs/DECISIONS.md` has a new entry explaining the change.

## Agent mirror-back (fill before coding starts)

Intent: delete the Java gateway and re-implement its two public endpoints inside ml-service
with byte-compatible success responses and the same error codes, so the frontend works
unchanged against `:8000`. Inputs/outputs: as in the tables above. Assumptions flagged:
the four deliberate differences listed above — each only affects direct API callers or
removes a failure mode, none changes what the UI shows for a valid request.
