# Spec: Buffalo disease detection (species architecture + interim reuse)

**Milestone**: M11
**Status**: superseded — Buffalo removed as a supported species (2026-09-22)

> **Superseded.** Buffalo support was removed from the application (backend `Species` enum,
> frontend `SPECIES_OPTIONS`, and a Flyway migration cleaning up any existing
> `species = 'BUFFALO'` rows). No usable buffalo symptom or image dataset was ever found
> across two separate searches months apart — it never moved past the disclosed cow-model
> approximation this spec originally shipped, and there was no realistic path to a real
> buffalo-trained model. Rather than keep carrying a species permanently stuck at
> "approximation," it was dropped. This spec is kept as-is (not rewritten) per this repo's
> convention of not editing history — see `docs/specs/M12-sheep-disease-detection.md`'s
> "Follow-up" section for what replaced this pattern for Sheep (a real, narrowly-scoped
> trained model) and the removal details. The species architecture itself (the `Animal`
> rename, the `species` field, the whole M11→M14 pattern) is unaffected — only the one
> species value is gone.

## Actor + goal

A farmer/vet with buffalo, not just cattle, can select "Buffalo" when submitting a
diagnosis and get a result — with the app's domain model generalized to represent "which
animal is this" for the first time, so M12–M14 (Sheep/Cat/Dog) can reuse the same pattern
without repeating this architecture discussion.

## Design decision: rename `Cattle` → `Animal` + `species` field

Per issue #20's own flagged open question — resolved here, not deferred further:

**Rename.** `Cattle`/`CattleController`/`CattleService`/`CattleRepository`/`CattleResponse`/
`CreateCattleRequest` → `Animal`/`AnimalController`/`AnimalService`/`AnimalRepository`/
`AnimalResponse`/`CreateAnimalRequest` (package `com.cattlecare.backend.cattle` →
`.animal`), `POST /api/cattle` → `POST /api/animals`, `diagnosis_case.cattle_id` →
`animal_id`, error codes `CATTLE_TAG_DUPLICATE`/`CATTLE_NOT_FOUND` → `ANIMAL_TAG_DUPLICATE`/
`ANIMAL_NOT_FOUND`.

**Why now, not deferred to M12**: 3 more species are already planned (M12–M14). Renaming
once now costs one migration + one mechanical rename across 3 services; deferring means
either doing this exact rename later anyway (after more code has accumulated depending on
the `Cattle` name) or leaving increasingly inaccurate naming in place as Sheep/Cat/Dog get
added to something still called "Cattle" everywhere in the code. This is a breaking API
change (`/api/cattle` → `/api/animals`, response field `cattleId` → `animalId`) — acceptable
here per `docs/DECISIONS.md`'s standing position that this is a local/learning project with
no external consumers, so breaking changes don't need versioning ceremony.

**What does NOT change**: the product's public name/branding ("Cattle Disease Prediction
System", the repo name) — that's a separate, much bigger decision explicitly out of scope
here (see "Not in scope"). The frontend's `<h1>` copy changes minimally (see below), nothing
else about branding does.

## Design decision: interim model reuse, not a buffalo-specific model yet

**Blocker inherited from the same wall M9 hit**: no buffalo-specific symptom or image
dataset was found. Web research found real evidence that Foot and Mouth Disease and Lumpy
Skin Disease both affect buffalo (FMD: fever, lameness, vesicular lesions in mouth/feet,
consistent with cattle; LSD: confirmed via experimental infection studies, though buffalo
appear less naturally susceptible than cattle per the literature — a real, documented
difference, not assumed parity). A paper ("Buffalo Disease Diagnosis Using Machine
Learning: A Symptom-Based Text Classification Approach") references a buffalo-disease
dataset compiled from veterinary literature and a livestock-department website, but no
confirmed freely-downloadable copy was found — same "cited but not confirmed accessible"
situation as M9's Kaggle dataset before it was confirmed. No buffalo-specific image dataset
was found at all.

**Decision**: ship a real, working buffalo diagnosis path now by **reusing the existing
cattle-trained symptom model** (`ml-service/app/models/symptom_model.py`, unchanged) for
buffalo submissions too, rather than blocking this entire milestone on unavailable data —
explicitly disclosed as an approximation, not a buffalo-specific trained model. This mirrors
M8's "wire the pipeline, disclose the limitation, real model later" pattern. `species` is
captured on the `Animal` record and shown in the UI, but **does not change ml-service's
request/response contract in this milestone** — that's real scope for a real future dataset,
not something to fake now.

## Boundaries & failure states

- `species` is a `COW`/`BUFFALO` enum today, written to grow (`SHEEP`/`CAT`/`DOG` added in
  M12–M14, not here) — `@Enumerated(EnumType.STRING)`, not ordinal, so adding values later
  never shifts existing data.
- The frontend must make the "same model used for both" limitation visible, not silent —
  see Examples.
- `POST /api/animals` requires `species`; omitting it is a validation error
  (`VALIDATION_FAILED`, same shape as the existing blank-`tagNumber` case), not a silent
  default.
- Malformed JSON / an invalid `species` value (Jackson enum deserialization failure)
  currently has no dedicated handler in `GlobalExceptionHandler` — falls through to the
  generic catch-all, the same raw-exception-leak class of bug fixed for
  `MethodArgumentNotValidException` in the M8 PR. Fixed here too, proactively, since this
  milestone is the first thing that can actually trigger it (an invalid `species` string).

## Examples

**Request** — `POST /api/animals`: `{"tagNumber": "BUF-001", "farmId": 42, "species": "BUFFALO"}`
**Response (`201`)**: `{"id": 12, "tagNumber": "BUF-001", "farmId": 42, "species": "BUFFALO", "createdAt": "..."}`

**Diagnosis for a buffalo** — same symptom form, same model, response unchanged in shape;
the frontend result view notes the model wasn't trained on buffalo-specific data when
`species !== "COW"`.

**Edge case — invalid species**: `{"tagNumber": "X", "farmId": 1, "species": "GOAT"}` →
`400` with a clean `{code, message, details}` error, not a raw Jackson exception dump.

## Not in scope

- Sheep/Cat/Dog (M12–M14) — but this milestone's `species` enum and `Animal` naming should
  need no further architecture discussion for them.
- A real buffalo-trained symptom or image model — blocked on data, tracked as explicit
  follow-up scope once a dataset is confirmed (same status as M9's cattle image model before
  the Kaggle dataset was found — the user may want to search for/provide one the same way).
- Renaming the product/repo itself ("Cattle Disease Prediction System") — a bigger, separate
  decision.
- Any change to ml-service's request/response contract — species stays a backend/frontend
  concept until a real per-species model exists to justify threading it further.

## Acceptance criteria

- [x] Spec written and agreed (this file), including the rename decision from issue #20.
- [x] Backend: `Cattle` → `Animal` rename complete (entity, repository, service, controller,
      DTOs, package, error codes), `species` field added, new Flyway migration (never
      editing `V1__init.sql`).
- [x] `GlobalExceptionHandler` gains a handler for malformed-JSON/invalid-enum requests
      (`HttpMessageNotReadableException`) — clean `{code, message, details}`, not a raw dump.
- [x] Frontend: species selector (Cow/Buffalo), identity fields component renamed and
      extended, API client paths updated, a visible disclosure when a non-Cow species is
      selected that the model isn't species-specific yet.
- [x] `docs/API_CONTRACTS.md` updated for the renamed endpoints, new error codes, and the
      `species` field. (`docs/ARCHITECTURE.md` didn't need changes — its diagrams are
      service-level, not endpoint-path-level.)
- [x] Buffalo/LSD-susceptibility nuance and the FMD/LSD overlap findings documented (this
      spec) rather than assumed.
- [x] Full build/test suite green across all three services — backend 17/17 (clean build),
      ml-service unaffected (36/2 skipped), frontend lint + 9/9 + build — plus manual
      end-to-end verification against the real running stack: created a Buffalo animal via
      `POST /api/animals`, confirmed the species disclosure rendered, submitted symptoms,
      and confirmed the diagnosis correctly escalated (`Foot and Mouth Disease`,
      `escalate_to_vet`) using the shared cattle-trained model, exactly as designed. Also
      directly verified the new `INVALID_REQUEST_BODY` error path with a malformed
      `species` value via `curl`.

## Agent mirror-back

**Intent**: generalize the domain model once, now, before 3 more species arrive — and ship
a real (if approximate, disclosed) buffalo diagnosis path today rather than blocking the
whole milestone on data that doesn't exist yet.

**Inputs/outputs**: `POST /api/animals` gains a required `species` field; diagnosis
endpoints move from `/api/cattle/...` to `/api/animals/...`; ml-service's contract is
unchanged.

**Assumptions flagged before coding**:
1. Rename executed now rather than asked about again — the issue itself flagged this as "a
   decision to resolve in the spec," and the reasoning (3 more species already planned) was
   already laid out when the issue was created; re-litigating it here would just repeat that
   reasoning without new information.
2. Interim model reuse, clearly disclosed — chosen over either (a) blocking this milestone
   entirely on an unconfirmed dataset, or (b) silently treating buffalo predictions as if
   they came from a buffalo-trained model. Flagging this prominently since it's the
   milestone's biggest simplification.
3. `GlobalExceptionHandler`'s new handler is a proactive fix, not a reported bug — including
   it because this milestone is the first thing that can actually exercise the failure mode
   (an invalid enum value over the wire), consistent with fixing the same class of bug found
   reactively in the M8 PR.
