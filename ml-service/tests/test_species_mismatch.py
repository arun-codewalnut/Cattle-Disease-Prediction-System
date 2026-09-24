"""
Species-mismatch detection — see docs/specs/species-classifier.md.

The behaviour being prevented, measured before the original version of this existed: 15 real
cat photos fed to the cattle model with COW selected returned `uncertain` 0 times, averaged
71% confidence, and included "Foot and Mouth Disease, 85%" — a reportable disease,
confidently, from a photo of a cat.

A wrong-species photo is refused outright rather than annotated: warning alongside a real
diagnosis was tried first and left a dog photo reading "Foot and Mouth Disease, 60% —
contact your veterinarian". The detector reports only that a photo *isn't* the selected
species, never what it is instead — the "what is it" guess is unreliable enough to tell
someone their cat looks like a dog; the negative is the part that holds up.

**This detector was rewritten** (docs/specs/species-classifier.md) after the user reported it
wasn't catching real mismatches — reproduced directly: 3/8 real dog photos submitted as Cow
came back a confident, escalating cattle-disease diagnosis. Root cause: the previous version
repurposed an unrelated ImageNet-1k classifier's raw class probabilities, which had collapsed
for Dog once its disease dataset became skin-lesion close-ups (v1→v2 dataset swap, M16). Now
uses `app/models/species_classifier.py`, a real classifier fine-tuned on this project's own
cat/cow/dog/goat photos — including both the v1 whole-body and v2 close-up dog photos as real
"Dog" ground truth, which is exactly what the old approach couldn't see.

Tests needing real photos skip when the datasets aren't present (they're gitignored), the
same convention the image-model tests use. The logic tests always run.
"""
import base64
import pathlib

import pytest

from app.models.species_gate import looks_like_a_different_species

_CAT_PHOTOS = pathlib.Path(__file__).resolve().parents[1] / "data" / "cat-images" / "healthy"
_COW_PHOTOS = pathlib.Path(__file__).resolve().parents[1] / "data" / "cattle-images" / "healthy"
_DOG_PHOTOS = pathlib.Path(__file__).resolve().parents[1] / "data" / "dog-images"
_GOAT_PHOTOS = pathlib.Path(__file__).resolve().parents[1] / "data" / "goat-images"


def _photos(folder, limit):
    if not folder.is_dir():
        return []
    files = sorted(f for f in folder.rglob("*") if f.suffix.lower() in {".jpg", ".jpeg", ".png"})
    return files[:limit]


def test_no_warning_without_a_selected_species():
    assert looks_like_a_different_species(b"whatever", None) is False


def test_no_warning_for_a_species_this_project_does_not_model():
    assert looks_like_a_different_species(b"whatever", "HORSE") is False


def test_undecodable_bytes_never_raise_and_never_warn():
    # An advisory check must not be the thing that breaks a diagnosis.
    assert looks_like_a_different_species(b"not an image at all", "COW") is False


@pytest.mark.skipif(not _photos(_CAT_PHOTOS, 1), reason="no cat photos available locally")
def test_cat_photos_submitted_as_cow_are_flagged():
    flagged = [looks_like_a_different_species(p.read_bytes(), "COW") for p in _photos(_CAT_PHOTOS, 8)]
    assert sum(flagged) >= 5


@pytest.mark.skipif(not _photos(_COW_PHOTOS, 1), reason="no cattle photos available locally")
def test_cow_photos_submitted_as_cow_are_not_flagged():
    # The expensive error is a false reject on a valid photo — measured at ~7.7% overall on
    # the classifier's held-out validation split, so a small sample should mostly be clean.
    flagged = [looks_like_a_different_species(p.read_bytes(), "COW") for p in _photos(_COW_PHOTOS, 8)]
    assert sum(flagged) <= 1


@pytest.mark.skipif(not _photos(_COW_PHOTOS, 1), reason="no cattle photos available locally")
def test_cow_photos_submitted_as_cat_are_flagged():
    flagged = [looks_like_a_different_species(p.read_bytes(), "CAT") for p in _photos(_COW_PHOTOS, 8)]
    assert sum(flagged) >= 5


@pytest.mark.skipif(not _photos(_CAT_PHOTOS, 1), reason="no cat photos available locally")
def test_message_never_claims_what_the_animal_is():
    from app.agent.graph import _species_mismatch_message

    message = _species_mismatch_message("COW")
    assert "doesn't look like a cow" in message
    assert "no diagnosis was made" in message
    # Naming the wrong animal is the failure mode this wording exists to avoid.
    for other in ("cat", "dog", "sheep"):
        assert other not in message.lower()


# The reported bug, reproduced directly against real dog photos from the CURRENT (v2,
# skin-close-up) dataset — this is exactly what regressed and is exactly what needed to work
# again, not the retained v1 whole-body set (that's still used separately by the species
# classifier's own training data, see training/species_classifier_train.py, but this test
# validates the actual production photo set).
@pytest.mark.skipif(not _photos(_DOG_PHOTOS, 1), reason="no dog photos available locally")
def test_dog_photo_submitted_as_cow_is_refused_not_diagnosed():
    from app.agent.graph import run_diagnosis

    refused = 0
    for photo in _photos(_DOG_PHOTOS, 10):
        result = run_diagnosis({}, image_base64=base64.b64encode(photo.read_bytes()).decode(), species="COW")
        if result["diagnosis"] == "species_mismatch":
            refused += 1
            assert result["confidence"] == 0.0
            assert result["recommended_action"] == "retry_upload"
            # No disease guidance may ride along with a refusal.
            assert result["precautions"] == []
            assert result["next_steps"] == []
        else:
            # Whatever slips through must never be a reportable disease escalation — this is
            # the actual bug that was reported ("Foot and Mouth Disease" for a dog photo).
            assert result["recommended_action"] != "escalate_to_vet", (
                f"a dog photo produced {result['diagnosis']} with escalation"
            )
    # Class-weighted retraining (docs/DECISIONS.md) fixed Dog's own bias problem too — dog-as-
    # cow now catches ~92% on the classifier's held-out validation split, up from the collapsed
    # ~30% the previous ImageNet-heuristic version had.
    assert refused >= 7


@pytest.mark.skipif(not _photos(_GOAT_PHOTOS, 1), reason="no goat photos available locally")
def test_goat_photos_submitted_as_goat_are_not_flagged():
    flagged = [looks_like_a_different_species(p.read_bytes(), "GOAT") for p in _photos(_GOAT_PHOTOS, 10)]
    assert sum(flagged) <= 2


@pytest.mark.skipif(not _photos(_CAT_PHOTOS, 1), reason="no cat photos available locally")
def test_cat_photos_submitted_as_goat_are_flagged():
    flagged = [looks_like_a_different_species(p.read_bytes(), "GOAT") for p in _photos(_CAT_PHOTOS, 8)]
    assert sum(flagged) >= 5


# Goat and cow are the two most visually similar ruminants in this project's own photos —
# the weakest pair in the system even after class-weighted retraining fixed the classifier's
# original COW bias (see docs/DECISIONS.md), but no longer a low number: ~93% on the
# classifier's own held-out validation split.
@pytest.mark.skipif(not _photos(_GOAT_PHOTOS, 1), reason="no goat photos available locally")
def test_goat_photos_submitted_as_cow_are_flagged():
    flagged = [looks_like_a_different_species(p.read_bytes(), "COW") for p in _photos(_GOAT_PHOTOS, 10)]
    assert sum(flagged) >= 7


@pytest.mark.skipif(not _photos(_COW_PHOTOS, 1), reason="no cattle photos available locally")
def test_matching_photo_still_gets_a_real_diagnosis():
    from app.agent.graph import run_diagnosis

    for photo in _photos(_COW_PHOTOS, 5):
        result = run_diagnosis({}, image_base64=base64.b64encode(photo.read_bytes()).decode(), species="COW")
        assert result["diagnosis"] != "species_mismatch"
