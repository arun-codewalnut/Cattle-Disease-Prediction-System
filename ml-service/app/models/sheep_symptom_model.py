"""
Sheep symptom-based PPR screen — inference.

See docs/specs/M12-sheep-disease-detection.md's follow-up section and
data/sheep-symptoms/SOURCE.md. Unlike `symptom_model.py` (5-disease cattle model), this is a
narrow, single-disease binary screen: PPR (Peste des Petits Ruminants) positive/negative,
trained on real field-collected goat+sheep clinical data. `FEATURES` and `DISEASES` here are
the canonical schema — the training script imports them from this module rather than
redefining them, same convention as `symptom_model.py`.

A negative result means "not PPR," not "healthy" — this model was never trained to recognize
any other disease, so it can't rule anything else out. The frontend discloses this.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import xgboost as xgb

FEATURES = [
    "temp",
    "nasal_discharge",
    "diarrhea",
    "difficult_breathing",
    "eye_discharge",
    "oral_nasal_lesion",
]

DISEASES = [
    "PPR Negative",
    "PPR (Peste des Petits Ruminants)",
]

CONFIDENCE_THRESHOLD = 0.4

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "sheep_symptom_model.pkl"

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
    """Predict PPR positive/negative from a symptom dict. Unknown keys in `symptoms` are
    ignored; missing/None values are treated as missing data, not as "symptom absent" —
    same convention as symptom_model.predict()."""
    provided = sum(1 for feature in FEATURES if symptoms.get(feature) is not None)
    if provided == 0:
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
