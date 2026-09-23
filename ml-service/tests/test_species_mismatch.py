"""
Species-mismatch warning — see docs/specs/species-mismatch-and-actionable-results.md.

The behaviour being prevented, measured before this existed: 15 real cat photos fed to the
cattle model with COW selected returned `uncertain` 0 times, averaged 71% confidence, and
included "Foot and Mouth Disease, 85%" — a reportable disease, confidently, from a photo of
a cat.

The detector reports only that a photo *isn't* the selected species, never what it is
instead. ImageNet carries 118 dog classes against 5 cat and 3 cattle, so the "what is it"
guess is unreliable enough to tell someone their cat looks like a dog; the negative is the
part that holds up.

Tests needing real photos skip when the datasets aren't present (they're gitignored), the
same convention the image-model tests use. The logic tests always run.
"""
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
def test_warning_text_never_claims_what_the_animal_is():
    from app.agent.graph import _species_warning

    message = _species_warning("COW")
    assert "doesn't look like a cow" in message
    # Naming the wrong animal is the failure mode this wording exists to avoid.
    for other in ("cat", "dog", "sheep"):
        assert other not in message.lower()
