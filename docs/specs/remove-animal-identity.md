# Spec: Remove animal identity (tag number, farm ID, and the animal record)

**Milestone**: stretch (post-M15 refactor)
**Status**: agreed

## Actor + goal

A farmer/vet wants a diagnosis for a species, and nothing else. Today the UI makes them
invent an animal tag number and a farm ID first, and the backend creates an `animal` row
before it will accept any diagnosis — none of which the prediction uses. `ml-service` has
never known about tags or farms: `POST /agent/diagnose` takes `symptoms`, an image, and
`species` only.

The goal is to delete animal identity from the product entirely: the fields, the entity, the
table, the routes, and the docs. `species` stays — it genuinely routes to a different trained
model (Sheep → PPR, Cat/Dog → their image models) and gates which diagnosis modes are
allowed.

Diagnosis history survives as a flat list of `diagnosis_case` rows carrying their own
`species`, rather than rows grouped under an animal.

## Boundaries & failure states

- **Case history is not removed.** `diagnosis_case` keeps every column it has except
  `animal_id`, and gains `species`. Cases stop being groupable by animal — that is the
  accepted cost of removing identity, and is the user's explicit decision.
- **Species validation stays exactly as-is.** Symptom diagnosis stays rejected for Cat/Dog
  (`DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`, 400); image diagnosis stays allowed for
  Cow/Sheep/Cat/Dog. An unknown species string stays `INVALID_REQUEST_BODY` (400) via the
  existing `HttpMessageNotReadableException` handler.
- **A missing or null `species` in the request body is a validation failure**
  (`VALIDATION_FAILED`, 400) — it is not defaulted to `COW`. Silently guessing a species
  would silently pick a different trained model, which is exactly the class of bug
  `docs/DISCLAIMER.md` exists to prevent.
- **Error codes that only described identity conflicts are deleted, not renamed**:
  `ANIMAL_TAG_DUPLICATE` and `ANIMAL_NOT_FOUND` have no remaining trigger once the routes
  are gone.
- **The ml-service contract does not change at all.** No request or response field is added,
  removed, or renamed on `POST /agent/diagnose`.
- **The existing `animal` table is dropped by a new forward migration** (`V4`), never by
  editing `V1`/`V2`/`V3` — those have already run against real databases. Dropping the table
  discards existing animal rows and the `animal_id` link on historical cases; those cases
  keep their diagnosis, confidence, symptoms, correlation ID, and timestamp.
- Failure behavior that must not regress: if `ml-service` is unreachable or errors, no case
  is persisted (`ML_SERVICE_UNAVAILABLE` / `ML_SERVICE_ERROR`); image validation
  (count/type/size) still runs before any ml-service call.

## Examples

**Symptom diagnosis** — `POST /api/diagnoses`
```json
{ "species": "COW", "symptoms": { "fever": true, "mouthLesions": true } }
```
→ `201`
```json
{
  "id": 7,
  "species": "COW",
  "diagnosis": "Foot and Mouth Disease",
  "confidence": 0.81,
  "explanation": "Predicted Foot and Mouth Disease with 81% confidence.",
  "recommendedAction": "escalate_to_vet",
  "precautions": ["Isolate the affected animal from the rest of the herd immediately."],
  "nextSteps": ["Contact your veterinarian or local animal health authority immediately."],
  "createdAt": "2026-09-22T10:00:00Z"
}
```

**Image diagnosis (1–5 photos)** — `POST /api/diagnoses/image`, `multipart/form-data` with
a `species` field and 1–5 `images` parts → `201` with the existing
`{ "results": [...], "diagnosesAgree": true|false }` shape, each result carrying `species`.

**Edge case — symptom diagnosis for a cat**: `{ "species": "CAT", "symptoms": {} }` →
`400 DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES` before any ml-service call, same as today.

**Edge case — missing species**: `{ "symptoms": { "fever": true } }` →
`400 VALIDATION_FAILED` with `details: { "species": "must not be null" }`.

**Edge case — 6 photos**: still `400 TOO_MANY_IMAGES`, rejected before the ml-service call.

## Not in scope

- Removing or redesigning diagnosis history itself (the table, the correlation ID, the
  persisted columns) — only the `animal_id` link goes.
- Any change to `ml-service`, its models, its API, or its tests.
- Adding a replacement identity concept (owner, session, account). If identity returns
  later, it returns as a new spec, not by reviving this one.
- Backfilling `species` for historical `diagnosis_case` rows from the dropped `animal`
  table — see "Assumptions" in the mirror-back below.
- A read/list endpoint for case history (none exists today).

## Acceptance criteria (must be checkable)

- [ ] No file under `backend/src/main/java` mentions `tagNumber`, `farmId`, `Animal`,
      `AnimalService`, `AnimalRepository`, `ANIMAL_TAG_DUPLICATE`, or `ANIMAL_NOT_FOUND`.
- [ ] `Species` still exists and is still forwarded to `ml-service` on every call.
- [ ] `POST /api/diagnoses` and `POST /api/diagnoses/image` exist; `POST /api/animals` and
      both `/api/animals/{id}/diagnoses*` routes return 404.
- [ ] Migration `V4` drops `diagnosis_case.animal_id`, adds `diagnosis_case.species`
      (NOT NULL), and drops the `animal` table. `V1`–`V3` are byte-identical to before.
- [ ] No file under `frontend/src` mentions `tagNumber`, `farmId`, or `createAnimal`; the
      form renders a species selector and no identity inputs.
- [ ] The UI performs exactly **one** HTTP request per diagnosis submission (was two).
- [ ] `cd backend && ./mvnw -B verify` passes.
- [ ] `cd frontend && npm run lint && npm test && npm run build` all pass.
- [ ] `cd ml-service && pytest` passes unchanged (proves nothing in ml-service was touched).
- [ ] `README.md` and `docs/API_CONTRACTS.md` contain no tag-number/farm-ID instructions,
      and the "Repeat visits for the same animal" section is gone.

## Agent mirror-back (fill before coding starts)

**Intent as I understand it**: delete the animal-identity concept end to end — not just hide
the two form fields. The user explicitly chose "drop the animal record entirely" over keeping
a thin `id + species` record, accepting that diagnosis cases stop being groupable by animal.

**Inputs/outputs that change**:
- In: `POST /api/animals {tagNumber, farmId, species}` then
  `POST /api/animals/{id}/diagnoses {symptoms}` (two calls).
- Out: `POST /api/diagnoses {species, symptoms}` (one call). Image path likewise collapses
  from two calls to one `POST /api/diagnoses/image` carrying `species` as a form field.
- `DiagnosisCaseResponse.animalId` → `species`.

**Assumptions I had to make** (flagging rather than silently choosing):
1. **`species` is required, never defaulted.** Defaulting to `COW` would quietly route a
   sheep case to the cattle model.
2. **Existing `diagnosis_case` rows are backfilled with their animal's species** inside V4
   *before* `animal_id` is dropped, rather than defaulting them all to `'COW'`. The join is
   still available at that point in the migration, so using it is both cheap and honest; any
   orphan row (impossible under the current NOT NULL FK, but defensive) falls back to `'COW'`
   so the NOT NULL constraint can be added.
3. **`Species` moves from `com.cattlecare.backend.animal` to
   `com.cattlecare.backend.diagnosis`**, since the `animal` package is being deleted and
   diagnosis is its only remaining consumer.
4. **`AnimalIdentityFields.jsx` becomes `SpeciesField.jsx`** rather than being deleted — the
   species selector and its per-species disclaimers live there and are still needed.
5. The correlation ID continues to be generated per submission in the frontend and forwarded;
   one call per submission now instead of two sharing one ID.
