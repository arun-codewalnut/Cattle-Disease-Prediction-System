"""
"Is this even a photo of an animal" gate — runs in front of every disease-specific image
model (cattle/cat/dog), using a pretrained, off-the-shelf ImageNet-1k classifier (no
fine-tuning, no new dataset). See docs/specs/M15-image-diagnosis-quality-gate.md.

Standard ImageNet-1k class ordering groups every living-creature class (fish/bird/reptile/
amphibian/mammal/arachnid/insect/crustacean) contiguously at indices 0-397; index 398
("abacus") onward is the first man-made/object class — verified directly against
`MobileNet_V2_Weights.DEFAULT.meta['categories']`, not assumed.

This deliberately does NOT try to confirm the photo is of the *correct* species — only
whether it's an animal at all. Verifying species match is a materially bigger, separate
problem (flagged and deferred in a prior session's HANDOFF.md); this gate only needs to catch
"someone uploaded a photo of a car," not "someone uploaded a dog photo while diagnosing a
cat" — the latter still reaches the disease classifier and, same as today, most likely comes
back "uncertain."
"""
from __future__ import annotations

import io

import torch
from PIL import Image, UnidentifiedImageError
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

# Verified empirically (see the spec) against real cattle/cat/dog photos and real
# non-animal (table, car) photos before relying on this boundary.
_ANIMAL_CLASS_MAX_INDEX = 397

_weights = MobileNet_V2_Weights.DEFAULT
_preprocess = _weights.transforms()
_model_cache: torch.nn.Module | None = None


def _get_model() -> torch.nn.Module:
    global _model_cache
    if _model_cache is None:
        model = mobilenet_v2(weights=_weights)
        model.eval()
        _model_cache = model
    return _model_cache


def is_animal_photo(image_bytes: bytes, top_k: int = 5) -> bool:
    """True if any of the top-`top_k` ImageNet-1k predictions is an animal class.

    Deliberately lenient (top-5, not top-1): a real photo's single best guess can land on
    the wrong animal class entirely (e.g. a real dog photo's top-1 prediction was "web site"
    in testing) while still having a correct animal class further down — top-5 catches that,
    top-1 alone would have false-rejected a genuinely valid photo.

    Undecodable bytes return True (fail open) — that case is already handled upstream as
    "uncertain" by predict_image_node's own PIL-decode step; this function should never be
    the one deciding an already-broken image is invalid, only a successfully-decoded one
    that just isn't an animal.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except (UnidentifiedImageError, OSError):
        return True

    model = _get_model()
    tensor = _preprocess(image).unsqueeze(0)
    with torch.no_grad():
        logits = model(tensor)

    top_indices = torch.topk(logits[0], top_k).indices.tolist()
    return any(idx <= _ANIMAL_CLASS_MAX_INDEX for idx in top_indices)
