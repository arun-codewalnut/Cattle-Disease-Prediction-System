"""
Real species classifier — inference.

Replaces `species_gate.py`'s old ImageNet-1k-class-heuristic approach to species-mismatch
detection (see `docs/specs/species-classifier.md`). That approach repurposed a generic
pretrained classifier's raw class probabilities (e.g. "ox", "water buffalo") as a proxy for
"does this look like a cow" — measured, after Dog's disease dataset moved to skin-lesion
close-ups, to have collapsed for Dog specifically: dog-as-cow catch rate dropped from ~80% to
~30%, because close-ups don't show the face/ears/snout features the generic ImageNet classes
key on. A **real classifier, fine-tuned on this project's own photos** (including those exact
close-ups as real "Dog" ground truth) fixes the root cause rather than tuning a threshold
around it.

`SPECIES` are the 4 classes with real local photo data: `CAT`, `COW`, `DOG`, `GOAT`. `SHEEP`
has no photos of its own anywhere in this project (same wall its symptom model's SOURCE.md
documents) — Sheep photos are already routed to the cattle disease model as a disclosed
approximation, so Sheep is mapped to the `COW` class for this check too, same grouping
`species_gate.py` used before.

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

SPECIES = ["CAT", "COW", "DOG", "GOAT"]

# Species this project has no photos for at all — mapped onto the closest class with real
# data for this check's purposes. Sheep photos already fall back to the cattle disease model
# (docs/DECISIONS.md), so COW is the right proxy here too.
SPECIES_ALIAS = {"SHEEP": "COW"}

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "species_classifier.pt"

_artifact_cache: dict[str, torch.nn.Module] = {}


def _load_artifact(model_path: Path) -> torch.nn.Module:
    key = str(model_path)
    if key not in _artifact_cache:
        if not model_path.exists():
            raise FileNotFoundError(model_path)
        model = build_model(len(SPECIES))
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.eval()
        _artifact_cache[key] = model
    return _artifact_cache[key]


def predict_probabilities(image_bytes: bytes, model_path: Path | None = None) -> dict[str, float] | None:
    """Returns `{species: probability}` over `SPECIES`, or `None` for undecodable bytes —
    the caller (`species_gate.looks_like_a_different_species`) already treats that as "can't
    tell, don't flag" the same way it always has."""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except (UnidentifiedImageError, OSError):
        return None

    model = _load_artifact(model_path or DEFAULT_MODEL_PATH)

    tensor = PREPROCESS(image).unsqueeze(0)
    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1)[0]

    return {species: float(probs[i]) for i, species in enumerate(SPECIES)}
