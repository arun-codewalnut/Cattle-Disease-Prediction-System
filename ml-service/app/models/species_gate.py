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

# How much of the prediction has to land on animal classes for the photo to count as one.
# Chosen by measurement — see is_animal_photo's docstring for the table.
_MIN_ANIMAL_MASS = 0.30

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


def is_animal_photo(image_bytes: bytes) -> bool:
    """True if the photo is, on balance, of an animal.

    Measured as the total probability mass over ImageNet's animal classes, not by whether an
    animal class appears in the top-k. The top-5 membership test this replaced was far too
    lenient, and for a structural reason: **398 of the 1000 classes are animals**, so nearly
    any cluttered image lands one of them in its top five by chance. A screenshot of text
    uploaded with Dog selected passed that gate and came back "Kennel Cough, 42%".

    Measured on 12 non-animal images (text/UI/chart/code screenshots, solid colours, plus the
    car and table fixtures) and 90 real animal photos across all three trained species:

    | rule                     | non-animals let through | real photos rejected |
    |--------------------------|------------------------|----------------------|
    | any of top-5 is animal   | 2/12                   | 2/90                 |
    | animal mass >= 0.30      | **0/12**               | 2/90                 |

    Same cost in false rejections, and it stops everything the old rule let through. The 2%
    that are rejected are extreme close-ups, which is why the caller's message asks for a
    clearer photo of the animal.

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
        probabilities = torch.softmax(model(tensor)[0], dim=0)

    animal_mass = float(probabilities[: _ANIMAL_CLASS_MAX_INDEX + 1].sum())
    return animal_mass >= _MIN_ANIMAL_MASS


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
    # Cow, sheep and goat share one group. There is no sheep or goat-disease image model —
    # those photos are routed to the cattle (sheep) or a binary (goat) model as disclosed
    # approximations/limitations — so refusing one for looking bovine/ruminant would reject
    # something the app supports by design. ImageNet-1k has no dedicated "goat" class (verified
    # directly against the weights' category list, M16) — "ibex" (350, a wild goat) is the
    # closest available proxy, added here.
    "RUMINANT": (345, 346, 347, 348, 349, 350),  # ox, water buffalo, bison, ram, bighorn, ibex
    "CAT": (281, 282, 283, 284, 285),        # 383 "Madagascar cat" is a lemur — excluded
    "DOG": tuple(range(151, 269)),
}

_SPECIES_TO_GROUP = {"COW": "RUMINANT", "SHEEP": "RUMINANT", "GOAT": "RUMINANT", "CAT": "CAT", "DOG": "DOG"}

# Each group scores by its PEAK class probability, not its sum or mean. This choice matters
# more than the threshold, because ImageNet carries 118 dog classes against 6 ruminant and 5
# cat:
#   - summing gives dog a structural advantage and refused 7.5% of genuine cattle photos;
#   - dividing by class count over-corrects the other way (a dog photo concentrates on one
#     breed, not 118), and dropped dog-as-cow detection to 7%;
#   - the peak is scale-free and does neither.
# Refuse only when another group's peak beats the selected one by this factor. Set from the
# measured distributions rather than by feel — on valid photos the ratio has a median near
# 0.9 and a 95th percentile around 24, while a genuine dog-as-cow sits at a median of 98 and
# cat-as-cow at 170. 25 sits in that gap: roughly 5% of valid photos refused, ~70% of
# dog-as-cow and ~85% of cat-as-cow caught.
_OTHER_SPECIES_PEAK_RATIO = 25.0

# Below this the model has no real opinion about any group (an animal this project doesn't
# model, say a horse). Allowing it through is the conservative choice — the caller has
# already established that it is an animal.
_GROUP_SIGNAL_FLOOR = 0.001


def looks_like_a_different_species(image_bytes: bytes, selected_species: str | None) -> bool:
    """True when another species is overwhelmingly the better match for this photo.

    Deliberately does **not** report which species that is. Cat photos frequently score
    higher on dog classes than cat ones, so naming the winner would tell a farmer "this looks
    like a dog" about their cat. The reliable signal is the comparison, not the label, so
    that is all this reports and all the message claims.

    False means "nothing worth refusing on": a matching photo, a species this project doesn't
    model, an undecodable image, or an animal none of the three groups recognise.

    **Livestock photos submitted under Cat or Dog are effectively not caught**, and no
    threshold fixes that: measured, a cow photo with Dog selected produces a ratio whose
    median (3.9) sits *below* the 90th percentile of genuinely valid cat photos (10.4). The
    distributions overlap, so any threshold that caught it would refuse valid pet photos at a
    far higher rate. This is a guard against the common mistake — a pet photo submitted under
    livestock — not a guarantee in both directions.

    Never raises — a diagnosis must not fail because this check could not run.
    """
    group = _SPECIES_TO_GROUP.get(selected_species or "")
    if group is None:
        return False

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        model = _get_model()
        tensor = _preprocess(image).unsqueeze(0)
        with torch.no_grad():
            probabilities = torch.softmax(model(tensor)[0], dim=0)
    except (UnidentifiedImageError, OSError, ValueError):
        return False

    peaks = {
        name: float(probabilities[list(indices)].max())
        for name, indices in _SPECIES_CLASS_INDICES.items()
    }
    if max(peaks.values()) <= _GROUP_SIGNAL_FLOOR:
        return False

    selected_peak = peaks[group]
    best_other = max(peak for name, peak in peaks.items() if name != group)
    return best_other >= _OTHER_SPECIES_PEAK_RATIO * max(selected_peak, 1e-9)
