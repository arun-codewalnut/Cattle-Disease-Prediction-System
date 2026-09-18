# Spec: Image-based disease recognition — phase 1 (pipeline, placeholder classifier)

**Milestone**: M8 (phase 1 of 2 — see "Not in scope")
**Status**: in progress

## Actor + goal

A farmer/vet uploads a photo (e.g. of a visible symptom) instead of ticking symptom
checkboxes, and gets back a diagnosis card in the same shape and with the same safety
behavior as the existing symptom-based flow — even though there is no trained image model
yet. The goal of phase 1 is the plumbing (upload → backend → ml-service →
`predict_image` → explain → recommend → persisted case → rendered result), not diagnostic
accuracy.

## Boundaries & failure states

- No cattle-disease image dataset and no trained CNN exist anywhere in this repo. Per the
  discussion on issue #16, this is explicitly out of scope for phase 1 (see below).
- **Images are not persisted to disk.** The uploaded file is validated, base64-encoded, sent
  to `ml-service` inline in the request body, used for one placeholder prediction, and then
  discarded — nothing is written to the filesystem or database. This sidesteps storage,
  retention, and cross-container file-serving questions entirely for phase 1; it can be
  revisited in phase 2 if/when a real model needs to persist images for
  retraining/auditing. `DiagnosisCase` rows for image-based diagnoses store an empty
  `symptoms` map (no schema change needed).
- Accepted formats: `image/jpeg`, `image/png`. Max size: 5 MB. Anything else is rejected
  before it reaches `ml-service`, via the same `{code, message, details}` error shape as
  every other backend error (`UNSUPPORTED_IMAGE_TYPE` / `IMAGE_TOO_LARGE`, both `400`).
- The placeholder classifier is a **deterministic hash of the image bytes** (not a model) —
  same image always yields the same result, but the result has no relationship to actual
  animal health. Its explanation text says so explicitly and skips the LLM/RAG explain path
  entirely (unlike symptom-based diagnoses), so a placeholder result is never mistaken for a
  grounded one.
- The existing `REPORTABLE_DISEASES` escalation rule (`docs/DISCLAIMER.md`) still applies
  identically to image-based results — this is the one thing phase 1 must get exactly right,
  since it's the safety-critical behavior any future real model also depends on.
- `ml-service`'s `image_url` field (already present in the contract, unused until now) is
  also wired up for completeness — `ml-service` will attempt to fetch it (short timeout) and
  falls back to an `uncertain` result on any failure, the same "never blocks a diagnosis"
  pattern used elsewhere in the agent. The new backend endpoint added in this phase uses
  `image_base64` exclusively, since it doesn't need real file hosting; `image_url` remains
  available for a future caller that does.

## Examples

**Request** — `POST /api/cattle/{cattleId}/diagnoses/image` (multipart, field `image`):
a JPEG file, ≤ 5MB.

**Response (`201`)** — same shape as the symptom endpoint:
```json
{
  "id": 8,
  "cattleId": 1,
  "diagnosis": "Lumpy Skin Disease",
  "confidence": 0.5,
  "explanation": "This is a placeholder image-based prediction (Lumpy Skin Disease, 50% confidence). No trained image-recognition model exists yet — this result only demonstrates the upload-to-response pipeline and must not be used for any real decision.",
  "recommendedAction": "escalate_to_vet",
  "createdAt": "..."
}
```
Note `recommendedAction: escalate_to_vet` fires here exactly as it would for a real
diagnosis — the escalation rule doesn't know or care that the diagnosis came from a
placeholder.

**Edge case — oversized/unsupported file**: `POST .../diagnoses/image` with a 10MB file or a
`.gif` → `400 IMAGE_TOO_LARGE` / `400 UNSUPPORTED_IMAGE_TYPE`, `ml-service` never called, no
`DiagnosisCase` persisted.

**Edge case — `ml-service` unreachable**: identical to the existing symptom flow —
`503 ML_SERVICE_UNAVAILABLE`, nothing persisted.

## Not in scope

- Sourcing, licensing, or labeling a real cattle-disease image dataset.
- Training or evaluating a real CNN — that's phase 2, tracked as a future issue once a
  dataset exists, not opened yet.
- Persisting uploaded images to disk/object storage, or any retention policy for them (see
  Boundaries above — deliberately not needed for a byte-hash placeholder).
- Distinguishing image-based from symptom-based cases in case history/listing (no such
  listing endpoint exists yet regardless — same gap M4's spec already flagged).
- Any accuracy or confidence claims — the placeholder's fixed 0.5 confidence and hash-based
  diagnosis are explicitly not meaningful.

## Acceptance criteria

- [x] Spec written and agreed in `docs/specs/` before implementation.
- [x] `ml-service`: `predict_image` node returns a real (placeholder-backed) prediction
      instead of `501`, in the same response shape as `predict_symptoms`, routed through
      `explain`/`recommend` so escalation logic applies identically.
- [x] `ml-service`: placeholder is deterministic (same image bytes → same diagnosis) and its
      explanation text clearly states it's a non-diagnostic placeholder.
- [x] `backend`: new `POST /api/cattle/{cattleId}/diagnoses/image` endpoint — validates
      content-type/size, forwards as `image_base64`, persists a `DiagnosisCase`, returns the
      same `DiagnosisCaseResponse` shape as the symptom endpoint.
- [x] `frontend`: an image-upload control alongside the existing symptom checklist, using the
      same tag-number/farm-ID fields, rendering the result through the existing
      `DiagnosisResult` component (no duplication).
- [x] Tests: `ml-service` pytest for the placeholder node/endpoint (determinism +
      escalation), `backend` JUnit for the new endpoint (validation + success + ml-service
      failure), `frontend` Vitest for the upload flow.
- [x] `docs/API_CONTRACTS.md` updated for the new backend endpoint and the `image_base64`
      field.
- [x] Full build/test suite green across all three services, plus manual end-to-end
      verification against the real running stack (native `ml-service` + `backend` +
      `frontend`): image upload → placeholder diagnosis → escalation for a reportable
      disease, symptom-based flow regression-checked (still works), and unsupported image
      type correctly rejected with a `400`.

## Agent mirror-back

**Intent**: prove the whole upload → diagnosis → persisted-and-rendered-result path works
end to end, using a placeholder instead of a real model, so that swapping in a real CNN
later (phase 2) only touches the placeholder's replacement, not the pipeline around it.

**Inputs/outputs**: an image file in (frontend) → base64 in the backend→ml-service request →
a `DiagnoseResponse`-shaped result out, persisted and rendered exactly like a symptom-based
one.

**Assumptions flagged before coding**:
1. **No file storage** — the biggest scope decision. The alternative (save to disk, serve via
   a static URL, have `ml-service` fetch it) would exercise `image_url` more realistically,
   but adds storage-lifecycle and cross-container-networking questions this phase doesn't
   need to answer to prove the pipeline works. Base64 pass-through avoids all of that.
2. **Placeholder skips the LLM/RAG explain path** rather than reusing `explain_node`
   unchanged, specifically so a placeholder result's explanation can never look like a
   real grounded one (a real risk if it silently reused the same wording as symptom-based
   diagnoses).
3. **No new DB column/migration** — an image-sourced `DiagnosisCase` is indistinguishable
   from a symptom-based one with all-`false`/empty symptoms at the schema level. Acceptable
   for phase 1 per "Not in scope" above; flagged as a real, known limitation rather than
   silently designed around.
