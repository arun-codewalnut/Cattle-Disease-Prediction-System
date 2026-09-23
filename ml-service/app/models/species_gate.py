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


# --------------------------------------------------------------------------------------
# Species-mismatch detection (see docs/specs/species-mismatch-and-actionable-results.md)
#
# This blocks the diagnosis rather than annotating it. Warning alongside the result was tried
# first and was wrong: a dog photo submitted as a cow still rendered "Foot and Mouth Disease,
# 60% confidence" with "contact your veterinarian — this is a reportable disease" underneath,
# and a caveat above that does not undo a confident, escalating, wrong answer.
#
# Reuses the same pretrained model as the gate above — no new dependency, no new dataset.
# ImageNet-1k class indices grouped into this project's four species. Index 383 is
# "Madagascar cat", which is a lemur, and is deliberately excluded from CAT.
#
# The imbalance is severe and shapes everything below: ImageNet has 118 dog classes, 5 cat,
# 3 cattle and 2 sheep. Matching on raw top-k class membership therefore reads almost any
# close-up of fur or skin as a dog — measured at 40% false flags on real cattle lesion
# photos, which would have blocked exactly the photos this app exists to diagnose. Comparing
# *normalised probability mass per group* instead, with a floor below which the model is
# treated as having no opinion, measured 6% false warnings at 95% of real mismatches caught.
_SPECIES_CLASS_INDICES = {
    "DOG": frozenset(range(151, 269)),
    "CAT": frozenset(range(281, 286)),
    "COW": frozenset({345, 346, 347}),   # ox, water buffalo, bison — ImageNet has no plain "cow"
    "SHEEP": frozenset({348, 349}),      # ram, bighorn
}

# Below this much total mass across all four groups, the model has no real opinion about the
# species — common for close-up lesion photos. Silence is the correct output there.
_SPECIES_OPINION_FLOOR = 0.15

# Reject only when the selected species holds almost none of the mass. This gates a refusal,
# not a warning, so it is deliberately strict: measured at 2.7% false rejections of valid
# photos while catching 84% of genuine mismatches (a dog photo submitted as a cow).
_SELECTED_SPECIES_MIN_SHARE = 0.02

# Cow and sheep are treated as one group on purpose. There is no sheep image model — sheep
# photos are routed to the cattle model as a disclosed approximation (docs/DISCLAIMER.md) —
# so cow/sheep confusion is already accepted by design, and refusing a sheep photo for
# looking bovine would be rejecting something the app deliberately supports. It also removes
# a third of the false rejections outright.
_INTERCHANGEABLE_SPECIES = frozenset({"COW", "SHEEP"})


def looks_like_a_different_species(image_bytes: bytes, selected_species: str | None) -> bool:
    """True when the photo clearly doesn't look like `selected_species`.

    Deliberately does **not** report which species it looks like instead. That part is not
    trustworthy: with 118 dog classes against 5 cat and 3 cattle, cat photos frequently carry
    more mass on dog classes than cat ones, so naming the winner would tell a farmer "this
    looks like a dog" about their cat. What *is* reliable is the negative — that almost none
    of the mass sits on the selected species — so that is all this reports, and all the
    warning text claims.

    False means "nothing worth raising": a matching photo, a species this project doesn't
    model, an undecodable image, or a photo the model has no confident species opinion about
    (close-up lesion shots usually land here, and silence is right for them).

    Never raises — a diagnosis must not fail because an advisory check could not run.
    """
    if not selected_species or selected_species not in _SPECIES_CLASS_INDICES:
        return False

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        model = _get_model()
        tensor = _preprocess(image).unsqueeze(0)
        with torch.no_grad():
            probabilities = torch.softmax(model(tensor)[0], dim=0)
    except (UnidentifiedImageError, OSError, ValueError):
        return False

    mass = {
        species: float(probabilities[list(indices)].sum())
        for species, indices in _SPECIES_CLASS_INDICES.items()
    }
    total = sum(mass.values())
    if total <= _SPECIES_OPINION_FLOOR:
        return False

    if selected_species in _INTERCHANGEABLE_SPECIES:
        selected_mass = sum(mass[species] for species in _INTERCHANGEABLE_SPECIES)
    else:
        selected_mass = mass[selected_species]

    return (selected_mass / total) < _SELECTED_SPECIES_MIN_SHARE
