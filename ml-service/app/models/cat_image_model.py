"""
Real cat image classifier — inference.

M13 follow-up, see docs/specs/M13-cat-disease-detection.md. `DISEASES` here **replaces** M13's
originally-researched disease list (Feline Upper Respiratory Infection, Ringworm, FIV) — no
image data exists for URI or FIV in anything found; this is the real, available list instead.

Architecture (build_model/PREPROCESS) is shared with app/models/image_model.py — same
MobileNetV2-transfer-learning approach, different head size and weights.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import torch
from PIL import Image, UnidentifiedImageError

from app.models.image_model import PREPROCESS, build_model

DISEASES = ["Flea Allergy", "Healthy", "Ringworm", "Scabies"]

CONFIDENCE_THRESHOLD = 0.4

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "cat_image_model.pt"

_artifact_cache: dict[str, torch.nn.Module] = {}


def _load_artifact(model_path: Path) -> torch.nn.Module:
    key = str(model_path)
    if key not in _artifact_cache:
        if not model_path.exists():
            raise FileNotFoundError(model_path)
        model = build_model(len(DISEASES))
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.eval()
        _artifact_cache[key] = model
    return _artifact_cache[key]


def predict(image_bytes: bytes, model_path: Path | None = None) -> dict[str, Any]:
    """Same contract as app/models/image_model.py's predict() — see there for the full
    rationale on each branch."""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except (UnidentifiedImageError, OSError):
        return {"diagnosis": "uncertain", "confidence": 0.0, "top_features": []}

    model = _load_artifact(model_path or DEFAULT_MODEL_PATH)

    tensor = PREPROCESS(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1)[0]

    top_idx = int(torch.argmax(probs))
    confidence = float(probs[top_idx])

    if confidence < CONFIDENCE_THRESHOLD:
        return {"diagnosis": "uncertain", "confidence": round(confidence, 4), "top_features": []}

    return {"diagnosis": DISEASES[top_idx], "confidence": round(confidence, 4), "top_features": []}
