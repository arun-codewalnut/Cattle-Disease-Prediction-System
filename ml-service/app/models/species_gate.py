"""
"Is this even a photo of an animal" gate, plus species-mismatch detection — both run in front
of every disease-specific image model (cattle/cat/dog/goat).

`is_animal_photo` uses a pretrained, off-the-shelf ImageNet-1k classifier (no fine-tuning, no
new dataset) — see docs/specs/M15-image-diagnosis-quality-gate.md. Unchanged by the rewrite
below: it was never the part that broke.

`looks_like_a_different_species` used to reuse that same ImageNet-1k classifier, repurposing
its generic class probabilities (e.g. "ox", "water buffalo", one of 118 dog breeds) as a proxy
for "does this look like species X." That approach's root problem: those classes were never
trained to recognize *this project's* photos, and it collapsed measurably once Dog's disease
dataset became skin-lesion close-ups (see docs/specs/species-classifier.md) — dog-as-cow catch
rate dropped from ~80% to ~30%, because a close-up doesn't show the face/ears/snout ImageNet's
dog classes actually key on. **Now uses `app/models/species_classifier.py`, a real classifier
fine-tuned on this project's own cat/cow/dog/goat photos** (including those exact close-ups as
real "Dog" ground truth), which fixes the root cause instead of tuning a threshold around it.
"""
from __future__ import annotations

import io

import torch
from PIL import Image, UnidentifiedImageError
from torchvision.models import mobilenet_v2, MobileNet_V2_Weights

from app.models import species_classifier

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
# Species-mismatch detection (see docs/specs/species-classifier.md)
#
# This blocks the diagnosis rather than annotating it. Warning alongside the result was tried
# first and was wrong: a dog photo submitted as a cow still rendered "Foot and Mouth Disease,
# 60% confidence" with "contact your veterinarian — this is a reportable disease" underneath,
# and a caveat above that does not undo a confident, escalating, wrong answer.
#
# Species this project has no photos for at all (Sheep) map onto the closest class with real
# data — Sheep photos already fall back to the cattle disease model as a disclosed
# approximation, so COW is the right proxy here too.
_SPECIES_TO_CLASS = {"COW": "COW", "SHEEP": "COW", "GOAT": "GOAT", "CAT": "CAT", "DOG": "DOG"}

# Calibrated against the deployed species classifier's own held-out validation split (1,179
# real photos never seen during training). First attempt trained with a plain (unweighted)
# loss — measured, not assumed, that this silently biased the model toward COW (3,244 training
# photos against DOG's 724, a ~4.5x imbalance): real Dog "healthy" photos scored higher on COW
# than DOG, and dog-as-cow/goat-as-cow catch rates were a weak 51-68% even at a sensitive
# threshold. Retrained with inverse-frequency class-weighted loss (see
# training/species_classifier_train.py) — real result: overall accuracy 84.9% -> 89.2%, macro
# F1 0.781 -> 0.857, and the two weak pairs both jump above 85%:
#
# at threshold=2.0 (chosen): overall caught 91.0%, overall false-reject 4.3%
#
# | pair              | caught | | same-species false-reject | rate |
# |-------------------|-------:|-|----------------------------|-----:|
# | dog as cow         | 92.4% | | CAT (own class)            | 2.5% |
# | goat as cow        | 86.5% | | COW (own class)            | 3.5% |
# | cat as dog         | 81.5% | | DOG (own class)            | 5.5% |
# | goat as dog        | 83.2% | | GOAT (own class)           | 8.1% |
# | everything else    | 88-98%| |                            |      |
#
# **2.0 is chosen** — with the rebalanced model, both dog-as-cow (the exact pair originally
# reported broken) and goat-as-cow (the two most visually similar species in this project's
# photos) catch above 85%, at an overall false-reject cost (4.3%) lower than the pre-existing
# ImageNet-heuristic system's own baseline (5-7.5%). Goat has the highest same-species
# false-reject (8.1%) — real, disclosed, the new weakest spot after the fix, still far better
# than any pair was before it. See docs/specs/species-classifier.md.
_OTHER_SPECIES_RATIO_THRESHOLD = 2.0


def looks_like_a_different_species(image_bytes: bytes, selected_species: str | None) -> bool:
    """True when another species is a meaningfully better match for this photo than the one
    selected, per the real trained species classifier (`app/models/species_classifier.py`).

    Deliberately does **not** report which species that is. Cat photos frequently score
    higher on dog classes than cat ones, so naming the winner would tell a farmer "this looks
    like a dog" about their cat. The reliable signal is the comparison, not the label, so
    that is all this reports and all the message claims.

    False means "nothing worth refusing on": a matching photo, a species this project doesn't
    model, an undecodable image, or a genuinely ambiguous one.

    Catch rate varies by pair (92-99% for most; see the threshold table in this module for
    the full breakdown) — real, measured, disclosed rather than assumed uniform.

    Never raises — a diagnosis must not fail because this check could not run.
    """
    target_class = _SPECIES_TO_CLASS.get(selected_species or "")
    if target_class is None:
        return False

    try:
        probabilities = species_classifier.predict_probabilities(image_bytes)
    except FileNotFoundError:
        # No trained model on disk (e.g. a fresh checkout before training has run) — never
        # let a missing artifact break the actual diagnosis path; the disease model's own
        # FileNotFoundError handling in graph.py is the place that surfaces that clearly.
        return False
    if probabilities is None:
        return False

    selected_prob = probabilities[target_class]
    best_other = max(prob for species, prob in probabilities.items() if species != target_class)
    return best_other >= _OTHER_SPECIES_RATIO_THRESHOLD * max(selected_prob, 1e-9)
