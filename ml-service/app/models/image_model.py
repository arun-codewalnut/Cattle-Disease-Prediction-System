"""
Real cattle image classifier — inference.

See docs/specs/M9-cattle-image-classifier.md. `DISEASES` here is the canonical label order
saved into the trained artifact — the training script imports it from this module rather than
redefining it, same convention as `symptom_model.py`.

**4 of the symptom model's 5 `DISEASES` are covered here** (Mastitis added — see
docs/specs/cow-mastitis-image-classifier.md and data/cattle-images/SOURCE.md for the real,
smaller, manually-curated dataset behind it). Bovine Respiratory Disease still has no image
dataset — don't imply full parity with the symptom model.
"""
from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import torch
from PIL import Image, UnidentifiedImageError
from torch import nn
from torchvision import transforms
from torchvision.models import mobilenet_v2

DISEASES = ["Healthy", "Lumpy Skin Disease", "Foot and Mouth Disease", "Mastitis"]

CONFIDENCE_THRESHOLD = 0.4

DEFAULT_MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "image_model.pt"

# Public (not `_`-prefixed) so training/image_model_train.py can reuse the exact same
# preprocessing at train time — train/inference transform mismatch would silently wreck
# accuracy without ever showing up as a bug in either place alone.
PREPROCESS = transforms.Compose(
    [
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

_artifact_cache: dict[str, nn.Module] = {}


def build_model(num_classes: int = len(DISEASES)) -> nn.Module:
    """Same architecture used at train and inference time: MobileNetV2 backbone, classifier
    head replaced for `num_classes` outputs. Not loading pretrained weights here — inference
    always loads a fine-tuned state_dict on top, and training loads pretrained weights itself
    before fine-tuning (see training/image_model_train.py). Shared by cat_image_model.py and
    dog_image_model.py too — same architecture, different head size and weights, not worth a
    second copy of this function for two extra callers."""
    model = mobilenet_v2(weights=None)
    model.classifier[1] = nn.Linear(model.last_channel, num_classes)
    return model


def _load_artifact(model_path: Path) -> nn.Module:
    key = str(model_path)
    if key not in _artifact_cache:
        if not model_path.exists():
            raise FileNotFoundError(model_path)
        model = build_model()
        model.load_state_dict(torch.load(model_path, map_location="cpu"))
        model.eval()
        _artifact_cache[key] = model
    return _artifact_cache[key]


def predict(image_bytes: bytes, model_path: Path | None = None) -> dict[str, Any]:
    """Predict a disease from raw image bytes. Undecodable bytes (not a real image, or a
    format PIL can't read) degrade to "uncertain" rather than raising — the caller (graph.py's
    predict_image_node) already handles the "couldn't even fetch the bytes" case; this handles
    "got bytes, but they're not a real image"."""
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

    return {
        "diagnosis": DISEASES[top_idx],
        "confidence": round(confidence, 4),
        # Per-pixel/region attribution (e.g. Grad-CAM) is a stretch goal, not required for M9
        # — see docs/specs/M9-cattle-image-classifier.md.
        "top_features": [],
    }
