"""
Species-mismatch warning — see docs/specs/species-mismatch-and-actionable-results.md.

The behaviour being prevented, measured before this existed: 15 real cat photos fed to the
cattle model with COW selected returned `uncertain` 0 times, averaged 71% confidence, and
included "Foot and Mouth Disease, 85%" — a reportable disease, confidently, from a photo of
a cat.

A wrong-species photo is refused outright rather than annotated: warning alongside a real
diagnosis was tried first and left a dog photo reading "Foot and Mouth Disease, 60% —
contact your veterinarian". The detector reports only that a photo *isn't* the selected
species, never what it is instead. ImageNet carries 118 dog classes against 5 cat and 3 cattle, so the "what is it"
guess is unreliable enough to tell someone their cat looks like a dog; the negative is the
part that holds up.

Tests needing real photos skip when the datasets aren't present (they're gitignored), the
same convention the image-model tests use. The logic tests always run.
"""
import base64
import pathlib

import pytest

from app.models.species_gate import looks_like_a_different_species

_CAT_PHOTOS = pathlib.Path(__file__).resolve().parents[1] / "data" / "cat-images" / "healthy"
_COW_PHOTOS = pathlib.Path(__file__).resolve().parents[1] / "data" / "cattle-images" / "healthy"


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
    # Advisory and deliberately conservative, so not every photo — but the clear majority.
    assert sum(flagged) >= 5


@pytest.mark.skipif(not _photos(_COW_PHOTOS, 1), reason="no cattle photos available locally")
def test_cow_photos_submitted_as_cow_are_not_flagged():
    # The expensive error is a false warning on a valid photo — measured at ~6% overall, so
    # a small sample should be clean.
    flagged = [looks_like_a_different_species(p.read_bytes(), "COW") for p in _photos(_COW_PHOTOS, 8)]
    assert not any(flagged)


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


# M16: the Dog *disease* dataset is now skin-lesion close-ups (see data/dog-images/SOURCE.md),
# not whole-dog photos. Measured, not assumed: close-ups give the ImageNet-based detector a
# much weaker species signal — 40-sample check went from 80% dog-as-cow caught (whole-body
# v1 photos) to 30% (v2 skin close-ups). That's a real, disclosed limitation of the detector
# for lesion-style photos generally (see docs/DECISIONS.md), not specific to this test. The
# superseded v1 folder is kept specifically as a stable whole-body-photo fixture so this test
# still validates the detector's real capability on a representative "someone submitted a
# photo of their dog" case, independent of whichever dataset currently trains the disease
# classifier.
_DOG_PHOTOS = pathlib.Path(__file__).resolve().parents[1] / "data" / "dog-images-v1-superseded"


@pytest.mark.skipif(not _photos(_DOG_PHOTOS, 1), reason="no dog photos available locally")
def test_dog_photo_submitted_as_cow_is_refused_not_diagnosed():
    # The reported bug, end to end through the agent: a dog photo with Cow selected used to
    # return "Foot and Mouth Disease, 60%" with escalation guidance attached.
    from app.agent.graph import run_diagnosis

    refused = 0
    for photo in _photos(_DOG_PHOTOS, 6):
        result = run_diagnosis({}, image_base64=base64.b64encode(photo.read_bytes()).decode(), species="COW")
        if result["diagnosis"] == "species_mismatch":
            refused += 1
            assert result["confidence"] == 0.0
            assert result["recommended_action"] == "retry_upload"
            # No disease guidance may ride along with a refusal.
            assert result["precautions"] == []
            assert result["next_steps"] == []
        else:
            # Whatever slips through must never be a reportable disease escalation.
            assert result["recommended_action"] != "escalate_to_vet", (
                f"a dog photo produced {result['diagnosis']} with escalation"
            )
    assert refused >= 4


# M16: real goat photos, now that Goat shares the RUMINANT group with Cow/Sheep (ibex added
# to that group as the closest available ImageNet proxy — no dedicated "goat" class exists).
_GOAT_PHOTOS = pathlib.Path(__file__).resolve().parents[1] / "data" / "goat-images"


@pytest.mark.skipif(not _photos(_GOAT_PHOTOS, 1), reason="no goat photos available locally")
def test_goat_photos_submitted_as_goat_are_not_flagged():
    # Measured at ~5% false-reject on a 40-photo sample (2/40) — slightly noisier than cow's,
    # since goat has no dedicated ImageNet class and leans on "ibex" as the closest proxy. A
    # small, non-random 10-photo slice can land more than one false flag by chance alone.
    flagged = [looks_like_a_different_species(p.read_bytes(), "GOAT") for p in _photos(_GOAT_PHOTOS, 10)]
    assert sum(flagged) <= 2


@pytest.mark.skipif(not _photos(_CAT_PHOTOS, 1), reason="no cat photos available locally")
def test_cat_photos_submitted_as_goat_are_flagged():
    flagged = [looks_like_a_different_species(p.read_bytes(), "GOAT") for p in _photos(_CAT_PHOTOS, 8)]
    assert sum(flagged) >= 5


@pytest.mark.skipif(not _photos(_COW_PHOTOS, 1), reason="no cattle photos available locally")
def test_matching_photo_still_gets_a_real_diagnosis():
    from app.agent.graph import run_diagnosis

    for photo in _photos(_COW_PHOTOS, 5):
        result = run_diagnosis({}, image_base64=base64.b64encode(photo.read_bytes()).decode(), species="COW")
        assert result["diagnosis"] != "species_mismatch"
