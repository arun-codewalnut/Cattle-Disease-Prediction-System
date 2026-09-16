# Spec: Baseline symptom-based disease classifier

**Milestone**: M1
**Status**: draft

## Actor + goal

A developer (later: the LangGraph agent) calls a Python function with a structured symptom
dict and gets back a disease prediction with a confidence score and a per-feature
explanation, trained on a public cattle disease dataset.

## Boundaries & failure states

- Input symptoms are a fixed, documented schema (see Examples) — unknown keys are ignored,
  not errored on, so the schema can grow without breaking callers.
- Missing symptom fields are allowed (real intake will be incomplete) — the model must
  handle missing values, not require every field.
- If the model's top prediction confidence is below `0.4`, return `"uncertain"` as the
  diagnosis rather than a low-confidence guess presented as if it were reliable.
- Training/inference code must not silently drop rows with missing labels — log and count
  them instead.

## Examples

**Input:**
```json
{"fever": true, "appetite_loss": true, "nasal_discharge": true, "milk_yield_drop": null}
```

**Expected output shape:**
```json
{
  "diagnosis": "Foot and Mouth Disease",
  "confidence": 0.78,
  "top_features": [
    {"feature": "fever", "contribution": 0.31},
    {"feature": "nasal_discharge", "contribution": 0.22}
  ]
}
```

**Edge case — all fields missing:**
```json
{}
```
→ `diagnosis: "uncertain"`, `confidence` below 0.4, `top_features: []`.

## Not in scope

- Image-based prediction (separate spec, later milestone).
- The FastAPI `/agent/diagnose` route wiring — that's M2, this spec covers only the
  trainable model + a plain Python inference function in `ml-service/app/models/`.
- Hyperparameter tuning beyond a reasonable default (cross-validated grid search is a
  stretch goal, not required for this milestone to be "done").

## Acceptance criteria

- [ ] Training script (`ml-service/training/symptom_model_train.py`) trains an XGBoost
      classifier on a documented public dataset and saves the artifact + a metadata entry
      in `ml-service/models/REGISTRY.md`.
- [ ] Model handles missing feature values without raising.
- [ ] `predict(symptoms: dict) -> dict` in `ml-service/app/models/symptom_model.py` returns
      the exact shape shown above.
- [ ] Below-threshold confidence returns `"uncertain"`, never a bare low-confidence label.
- [ ] SHAP (or equivalent) values back the `top_features` field — not a made-up ranking.
- [ ] Unit tests in `ml-service/tests/` cover: a confident prediction, the all-missing edge
      case, and at least one case per disease class in the dataset.
- [ ] Cross-validated accuracy/F1 per class logged via MLflow (or written to
      `ml-service/models/REGISTRY.md` if MLflow isn't wired up yet).

## Agent mirror-back

_(Fill this in before writing code — restate intent, inputs/outputs, and any assumptions.)_
