"""
Baseline symptom-based disease classifier — inference.

See docs/specs/M1-baseline-symptom-model.md for the full spec. `FEATURES` and `DISEASES`
here are the canonical schema — the data generator and training script both import from
this module rather than redefining it.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import xgboost as xgb

FEATURES = [
    "fever",
    "appetite_loss",
    "nasal_discharge",
    "milk_yield_drop",
    "mouth_lesions",
    "lameness",
    "excessive_salivation",
    "skin_nodules",
    "udder_swelling",
    "coughing",
    "labored_breathing",
]

DISEASES = [
    "Foot and Mouth Disease",
    "Lumpy Skin Disease",
    "Mastitis",
    "Bovine Respiratory Disease",
    "Healthy",
]

CONFIDENCE_THRESHOLD = 0.4

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "symptom_model.pkl"

_artifact_cache: dict[str, Any] = {}


def _load_artifact(model_path: Path) -> dict[str, Any]:
    key = str(model_path)
    if key not in _artifact_cache:
        with model_path.open("rb") as f:
            _artifact_cache[key] = pickle.load(f)
    return _artifact_cache[key]


def _vectorize(symptoms: dict[str, Any]) -> np.ndarray:
    row = []
    for feature in FEATURES:
        value = symptoms.get(feature)
        row.append(np.nan if value is None else float(bool(value)))
    return np.array([row], dtype=np.float32)


def predict(symptoms: dict[str, Any], model_path: Path | None = None) -> dict[str, Any]:
    """Predict a disease from a symptom dict. Unknown keys in `symptoms` are ignored;
    missing/None values are treated as missing data, not as "symptom absent"."""
    provided = sum(1 for feature in FEATURES if symptoms.get(feature) is not None)
    if provided == 0:
        # Zero evidence. XGBoost still produces a softmax output here via its learned
        # missing-value default-routing — but that's a training-time artifact, not a real
        # prediction, and empirically it can look confident. Reporting a uniform prior is
        # the honest answer to "what do you think with no information at all."
        return {
            "diagnosis": "uncertain",
            "confidence": round(1 / len(DISEASES), 4),
            "top_features": [],
        }

    artifact = _load_artifact(model_path or DEFAULT_MODEL_PATH)
    booster: xgb.Booster = artifact["booster"]
    label_names: list[str] = artifact["label_names"]

    x = _vectorize(symptoms)
    dmatrix = xgb.DMatrix(x, feature_names=FEATURES, missing=np.nan)

    probs = booster.predict(dmatrix)[0]
    top_idx = int(np.argmax(probs))
    confidence = float(probs[top_idx])

    if confidence < CONFIDENCE_THRESHOLD:
        return {"diagnosis": "uncertain", "confidence": round(confidence, 4), "top_features": []}

    contribs = booster.predict(dmatrix, pred_contribs=True)
    # multiclass pred_contribs shape: (n_samples, n_classes, n_features + 1) — last column is bias
    class_contribs = contribs[0][top_idx][:-1]
    ranked = sorted(zip(FEATURES, class_contribs), key=lambda pair: abs(pair[1]), reverse=True)
    top_features = [
        {"feature": name, "contribution": round(float(value), 4)}
        for name, value in ranked[:3]
        if abs(value) > 1e-6
    ]

    return {
        "diagnosis": label_names[top_idx],
        "confidence": round(confidence, 4),
        "top_features": top_features,
    }
