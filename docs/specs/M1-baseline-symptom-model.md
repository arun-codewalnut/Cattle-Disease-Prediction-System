# Spec: Baseline symptom-based disease classifier

**Milestone**: M1
**Status**: done

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

- [x] Training script (`ml-service/training/symptom_model_train.py`) trains an XGBoost
      classifier on a documented public dataset and saves the artifact + a metadata entry
      in `ml-service/models/REGISTRY.md`. (Dataset is synthetic, not real-public — see
      deviation #1 in the mirror-back above and `ml-service/data/synthetic-symptom-dataset/SOURCE.md`.)
- [x] Model handles missing feature values without raising.
- [x] `predict(symptoms: dict) -> dict` in `ml-service/app/models/symptom_model.py` returns
      the exact shape shown above.
- [x] Below-threshold confidence returns `"uncertain"`, never a bare low-confidence label.
      (Zero-evidence input is explicitly short-circuited to a uniform-prior confidence —
      see `predict()`'s docstring/comment.)
- [x] SHAP (or equivalent) values back the `top_features` field — not a made-up ranking.
      (XGBoost's native `pred_contribs=True`, TreeSHAP-equivalent — see deviation #2.)
- [x] Unit tests in `ml-service/tests/` cover: a confident prediction, the all-missing edge
      case, and at least one case per disease class in the dataset. (10/10 passing —
      `ml-service/tests/test_symptom_model.py`.)
- [x] Cross-validated accuracy/F1 per class logged via MLflow (or written to
      `ml-service/models/REGISTRY.md` if MLflow isn't wired up yet). (5-fold CV:
      accuracy 0.888, macro F1 0.888, per-class F1 0.809–0.922 — logged in REGISTRY.md.)

## Agent mirror-back

**Intent**: expose `predict(symptoms: dict) -> dict` as a standalone, testable Python
function (no API wiring — that's M2), backed by an XGBoost model trained by a separate
script, with feature-attribution explanations and an uncertainty threshold.

**Inputs**: a dict keyed by symptom name (from the fixed `FEATURES` list in
`app/models/symptom_model.py`), boolean or `None`/absent for unknown. Unrecognized keys
ignored.

**Outputs**: `{"diagnosis": str, "confidence": float, "top_features": [{"feature": str,
"contribution": float}]}` — `diagnosis` is `"uncertain"` and `top_features` is `[]` when
confidence is below `0.4`.

**Assumptions / deviations flagged before coding**:
1. **No real public dataset used.** A genuinely public, auth-free, ML-ready cattle-disease
   dataset wasn't reliably available to fetch in this environment (Kaggle-hosted ones need
   account/API auth). Using a clearly-labeled **synthetic** dataset instead — documented in
   `ml-service/data/synthetic-symptom-dataset/SOURCE.md` — with a realistic symptom/disease
   schema, so the training → inference → test pipeline is real and swapping in genuine data
   later only means replacing the CSV, not the code. Flagging this since the spec said
   "public cattle disease dataset" and this isn't literally that.
2. **Using XGBoost's built-in `pred_contribs=True`** (TreeSHAP-equivalent, computed by
   XGBoost's own C++ core) instead of the separate `shap` package, to avoid the
   already-documented Windows native-build blocker (`ml-service/AGENTS.md`). Satisfies the
   spec's "SHAP (or equivalent)" allowance.
3. MLflow isn't wired up — metrics written to `ml-service/models/REGISTRY.md`, as the spec
   allows.
