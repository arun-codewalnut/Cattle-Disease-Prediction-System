# Spec: Wire baseline model into FastAPI /agent/diagnose

**Milestone**: M2
**Status**: done

## Actor + goal

A caller (later: `backend`; for now, direct HTTP/tests) sends symptoms to
`POST /agent/diagnose` and gets back a real diagnosis from the M1 model — not the stub —
including a human-readable explanation and a `recommended_action` that enforces
[docs/DISCLAIMER.md](../DISCLAIMER.md)'s escalation constraint.

## Boundaries & failure states

- `image_url` stays accepted in the request schema but is ignored — image-based prediction
  is a later milestone.
- If the model artifact isn't trained/present on disk, the endpoint must return a structured
  `ApiError` (`code: "MODEL_NOT_TRAINED"`), never an unhandled 500 with a raw traceback.
- **Reportable/contagious diseases always escalate, regardless of confidence** — this is
  non-negotiable per `docs/DISCLAIMER.md`. `Foot and Mouth Disease` and `Lumpy Skin Disease`
  always return `recommended_action: "escalate_to_vet"`, even at high confidence, even
  though nothing else in this milestone reads confidence for routing.
- `"uncertain"` diagnoses always return `recommended_action: "consult_vet"` — never
  `"monitor"`.
- Response shape must exactly match `DiagnoseResponse` in `app/api/diagnose.py` and
  `docs/API_CONTRACTS.md` — this spec doesn't change the shape, only what fills it.

## Examples

**Input:**
```json
{"symptoms": {"fever": true, "mouth_lesions": true, "excessive_salivation": true}}
```

**Expected output (200):**
```json
{
  "diagnosis": "Foot and Mouth Disease",
  "confidence": 0.81,
  "explanation": "Predicted Foot and Mouth Disease with 81% confidence, based primarily on: mouth_lesions, excessive_salivation, fever.",
  "recommended_action": "escalate_to_vet",
  "sources": []
}
```

**Edge case — no symptoms provided:**
```json
{"symptoms": {}}
```
```json
{
  "diagnosis": "uncertain",
  "confidence": 0.2,
  "explanation": "Not enough symptom information was provided to make a confident prediction. Provide more symptom details or consult a vet directly.",
  "recommended_action": "consult_vet",
  "sources": []
}
```

**Edge case — model not trained** (e.g. `symptom_model.pkl` missing): `503` with
`{"code": "MODEL_NOT_TRAINED", "message": "...", "details": null}`.

## Not in scope

- LangGraph graph structure (M5) — this milestone keeps `run_diagnosis()` a direct function
  call, not a multi-node graph.
- RAG-grounded explanation (M6) — `explanation` here is a deterministic template string
  referencing the diagnosis, confidence, and top contributing features, not LLM-generated
  text. `sources` stays `[]`.
- Image-based prediction (separate, later milestone).

## Acceptance criteria

- [x] `run_diagnosis()` in `app/agent/graph.py` calls the real `symptom_model.predict()`
      instead of returning the stub.
- [x] `recommended_action` follows the explicit rule above: reportable diseases (FMD, LSD)
      → always `escalate_to_vet`; `"uncertain"` → always `consult_vet`; `"Healthy"` →
      `monitor`; any other diagnosed disease → `consult_vet`.
- [x] `explanation` is a templated string mentioning diagnosis, confidence, and (when
      present) the top contributing features — not hardcoded stub text.
- [x] Missing model artifact raises `ApiError(code="MODEL_NOT_TRAINED")`, caught by the
      existing global handler — not an unhandled exception.
- [x] Response shape unchanged from `DiagnoseResponse` / `docs/API_CONTRACTS.md`.
- [x] Tests (via FastAPI `TestClient`, hitting the real route) cover: a confident
      reportable-disease prediction (confirms escalation), the all-missing/uncertain case,
      a non-reportable diagnosed disease (confirms `consult_vet` not `escalate_to_vet`), and
      the model-not-trained error path. Existing `tests/test_health.py` tests still pass.
      (15/15 passing — `tests/test_diagnose_endpoint.py` + existing suites, all green on
      first run.)

## Agent mirror-back

**Intent**: replace `run_diagnosis()`'s stub body with a real call to M1's `predict()`,
add a small, explicit, auditable escalation rule (not model-driven) that operationalizes
the disclaimer's safety constraint, and a deterministic explanation template. Keep it a
plain function — LangGraph's actual graph structure is M5, not this milestone.

**Inputs/outputs**: unchanged from the existing stub's signature and the API's
`DiagnoseRequest`/`DiagnoseResponse` — this milestone changes what's *inside* `run_diagnosis`,
not the contract around it.

**Assumptions flagged before coding**:
1. **Escalation logic is a fixed lookup, not learned** — reportable-disease status is a
   short hardcoded list (`REPORTABLE_DISEASES` in `graph.py`), not derived from the model.
   This is deliberate: a safety rule like this should be auditable in code, not something
   the model could silently drift on.
2. **Tests need a real trained model.** Since `ml-service/models/*.pkl` is gitignored (no
   committed binary artifacts), tests train a real model into a temp path via M1's
   `training.symptom_model_train.train()`, same pattern as `test_symptom_model.py`. To
   support this without complicating the public API, `run_diagnosis()` gets an optional
   `model_path` parameter (default `None` → M1's `DEFAULT_MODEL_PATH`), forwarded to
   `predict()`.
3. The existing `tests/test_health.py::test_diagnose_stub` is renamed to
   `test_diagnose_basic_smoke` — it's no longer testing a stub, and the name was actively
   misleading once this lands.
