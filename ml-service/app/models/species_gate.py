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
# Chosen by measurement — see is_animal_photo's docstring for the table. Per-species, not a
# single global value: DOG's entire served dataset is skin-lesion close-ups, which this
# generic gate finds much harder than a whole-body shot (see the M16-follow-up history below),
# so DOG alone gets the lower, more lenient value. Every other species stays at the stricter
# 0.30 — measured to cost them almost nothing (COW/CAT/GOAT's own false-reject rates move by
# 1-2 points across the whole 0.25-0.30 range) while cutting non-animal false-accepts roughly
# 3x (see the "diagram/chart-style images" entry below).
_MIN_ANIMAL_MASS_DEFAULT = 0.30
_MIN_ANIMAL_MASS_BY_SPECIES = {"DOG": 0.25}

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


def is_animal_photo(image_bytes: bytes, selected_species: str | None = None) -> bool:
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
    | animal mass >= 0.30      | 0/12                   | 2/90                 |

    **Retuned to 0.25 for DOG only (M16 follow-up, then made per-species — see below)**, after
    full-scenario testing found this gate alone was rejecting 11.6% of real Dog photos — nearly
    double the 2% figure above — because Dog's disease dataset is now entirely skin-lesion
    close-ups (see `docs/specs/species-classifier.md`), which this generic gate finds harder
    than a whole-body shot.

    **A user-reported follow-up found the 0.25 value, applied globally, opened a different
    gap**: diagram/chart-style images (architecture diagrams, dashboards, flowcharts — flat
    vector graphics, not photos) were measured on a 50-image synthetic sample to pass this
    gate 12% of the time at 0.25, vs 2% at 0.30 — e.g. a component-diagram screenshot uploaded
    with Goat selected scored 0.261 and reached the (real, trained) health classifier, which
    duly produced a confident-sounding "55% Unhealthy" for an image that was never a goat photo
    at all. Raising the threshold back to 0.30 fixes that, but doing it globally would undo the
    Dog fix above — so **the threshold is per-species**, not a single global value:

    | species        | false-reject @ 0.25 | false-reject @ 0.30 | chosen |
    |----------------|---------------------|----------------------|--------|
    | DOG            | 5.2%                | 11.6%                | 0.25   |
    | COW            | 2.0%                | 3.2%                 | 0.30   |
    | CAT            | 0.8%                | 2.0%                 | 0.30   |
    | GOAT           | 8.4%                | 9.6%                 | 0.30   |

    Only Dog's own real photos are meaningfully sensitive to this knob (close-ups are
    genuinely harder for a generic gate); the other three species pay 1-2 points either way,
    so they get the stricter value and the much better (12% -> 2%) non-animal-diagram
    rejection it buys. Verified the three original non-animal fixtures stay rejected at both
    thresholds first (text-screenshot 0.21, car 0.13, table 0.07 — all comfortably below even
    the lower 0.25) so neither the M15 nor the M16 regression reopens.

    An unrecognized or missing `selected_species` (including symptom-only submissions, which
    never call this) falls back to the stricter 0.30 — the safer default when there's no
    Dog-specific reason to relax it.

    **Remaining, disclosed gap**: even at 0.30, 2% of the synthetic diagram sample still
    passed, and Dog specifically (which needs the lower threshold) still lets 12% of
    diagram-style images through — this generic, off-the-shelf classifier was never trained to
    recognize "diagram" as a concept, so a threshold on its animal-class mass can reduce but
    not eliminate this category, the same structural ceiling `docs/specs/species-classifier.md`
    already found and fixed for species-mismatch with a real trained classifier rather than a
    threshold. Not chased further this pass — see that spec's pattern if this is revisited.
    **Synthetic images (solid colours, random noise) remain a separately accepted, disclosed,
    pre-existing gap** (see `docs/DECISIONS.md`) — this gate is for real accidental mismatched
    uploads, not adversarial input.

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
    threshold = _MIN_ANIMAL_MASS_BY_SPECIES.get((selected_species or "").upper(), _MIN_ANIMAL_MASS_DEFAULT)
    return animal_mass >= threshold


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
