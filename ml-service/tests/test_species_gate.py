from pathlib import Path

from app.models.species_gate import is_animal_photo

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

# Real photos are .jpg, .jpeg, .png or (rarely) .gif depending on species — a glob for just
# "*.jpg" silently returns nothing for a species whose photos happen to be .jpeg, and every
# caller here treats "nothing found" as "skip this test" rather than an error. That is exactly
# what happened to Goat (all-.jpeg) until this was noticed: test_real_goat_photo_passes below
# had never actually run, in any session, since Goat's photo tests were added — a real gap in
# "did we test this," not just a hypothetical one.
_IMAGE_GLOBS = ("*.jpg", "*.jpeg", "*.png")


def _sample_species_photo(images_dir: str, folder: str) -> bytes:
    directory = Path(__file__).resolve().parents[1] / "data" / images_dir / folder
    for pattern in _IMAGE_GLOBS:
        path = next(directory.glob(pattern), None)
        if path is not None:
            return path.read_bytes()
    return None


def test_real_non_animal_photos_are_rejected():
    # Includes two diagram/chart-style fixtures (flat vector graphics, not photos) added after
    # a user-reported bug: a component-diagram screenshot uploaded with Goat selected scored
    # 0.261 animal-mass and passed the old, single-global 0.25 threshold, reaching the health
    # classifier and producing a confident-sounding "55% Unhealthy" for an image that was never
    # a goat at all. See species_gate.is_animal_photo's docstring for the measured fix
    # (per-species threshold) and the disclosed remaining gap.
    fixtures = (
        "non-animal-table.jpg",
        "non-animal-car.jpg",
        "non-animal-text-screenshot.png",
        "non-animal-diagram-flowchart.png",
        "non-animal-diagram-dashboard.png",
    )
    for fixture in fixtures:
        photo = (_FIXTURES_DIR / fixture).read_bytes()
        # No species selected (and every non-DOG species) uses the stricter 0.30 threshold —
        # this is the case that matters for the reported bug and the one all these fixtures
        # were verified against. DOG's own, more lenient threshold is covered separately below
        # since it's a real, disclosed, weaker guarantee, not the same claim.
        assert is_animal_photo(photo, "GOAT") is False, f"{fixture} was incorrectly treated as an animal photo"
        assert is_animal_photo(photo, None) is False, f"{fixture} was incorrectly treated as an animal photo"


def test_diagram_style_image_rejected_for_every_non_dog_species():
    # The exact reported pair (Goat selected, a diagram uploaded) plus its siblings — every
    # species that isn't Dog shares the stricter 0.30 threshold, so this should hold for all
    # of them, not just Goat.
    photo = (_FIXTURES_DIR / "non-animal-diagram-flowchart.png").read_bytes()
    for species in ("COW", "CAT", "GOAT", "SHEEP"):
        assert is_animal_photo(photo, species) is False, f"diagram passed for {species}"


def test_diagram_style_image_is_a_disclosed_remaining_gap_for_dog():
    # DOG intentionally keeps the more lenient 0.25 threshold (see the docstring's measured
    # trade-off table) because its dataset is all skin-lesion close-ups. This specific fixture
    # (mass 0.261) is a known, disclosed case that still passes for DOG specifically — asserted
    # here so that fact stays visible and intentional rather than accidentally "fixed" (and
    # therefore silently regressing Dog's own false-reject rate) by some future change.
    photo = (_FIXTURES_DIR / "non-animal-diagram-flowchart.png").read_bytes()
    assert is_animal_photo(photo, "DOG") is True


def test_undecodable_bytes_fail_open():
    # Not a real image at all — this function should never be the one rejecting garbage
    # bytes; predict_image_node's own PIL-decode step (in _fetch_image_bytes/predict_image_node)
    # already handles that case as "uncertain" before this ever runs.
    assert is_animal_photo(b"not a real image, just arbitrary bytes") is True


def test_real_cattle_photo_passes():
    photo = _sample_species_photo("cattle-images", "healthy")
    if photo is None:
        import pytest

        pytest.skip("no local ml-service/data/cattle-images — see its SOURCE.md")
    assert is_animal_photo(photo, "COW") is True


def test_real_cat_photo_passes():
    photo = _sample_species_photo("cat-images", "healthy")
    if photo is None:
        import pytest

        pytest.skip("no local ml-service/data/cat-images — see its SOURCE.md")
    assert is_animal_photo(photo, "CAT") is True


def test_real_dog_photo_passes():
    # DOG specifically, not the no-species default — this is the one species with its own,
    # more lenient threshold (see the docstring), so this needs to exercise that exact path,
    # not the stricter default every other species now shares.
    photo = _sample_species_photo("dog-images", "healthy")
    if photo is None:
        import pytest

        pytest.skip("no local ml-service/data/dog-images — see its SOURCE.md")
    assert is_animal_photo(photo, "DOG") is True


def test_real_goat_photo_passes():
    photo = _sample_species_photo("goat-images", "healthy")
    if photo is None:
        import pytest

        pytest.skip("no local ml-service/data/goat-images — see its SOURCE.md")
    assert is_animal_photo(photo, "GOAT") is True


def test_screenshot_of_text_is_rejected_end_to_end():
    """The reported bug: a screenshot of text uploaded with Dog selected came back
    "Kennel Cough, 42%". The old gate accepted it because it asked whether *any* of the
    top-5 classes was an animal, and 398 of ImageNet's 1000 classes are animals — so a
    cluttered image lands one there by chance. It's decided on probability mass now.
    """
    from app.agent.graph import run_diagnosis
    import base64

    photo = (_FIXTURES_DIR / "non-animal-text-screenshot.png").read_bytes()
    result = run_diagnosis({}, image_base64=base64.b64encode(photo).decode(), species="DOG")

    assert result["diagnosis"] == "invalid_image"
    assert result["recommended_action"] == "retry_upload"
    # No disease may be named, and no confidence invented, for something that was never
    # diagnosed.
    assert result["confidence"] == 0.0
    assert result["precautions"] == []
    assert result["next_steps"] == []


def test_diagram_uploaded_as_goat_is_rejected_end_to_end():
    """The exact user-reported bug: a component-diagram screenshot uploaded with Goat selected
    came back "Likely: Unhealthy (55% confidence)" — a real-looking result for an image that
    was never a photo of anything. Caused by the M16-follow-up threshold (0.25, applied
    globally) being too lenient for this image category; fixed by making the threshold
    per-species (Goat, like every non-Dog species, now uses 0.30). Must never again reach
    goat_image_model at all, let alone produce a confidence number.
    """
    from app.agent.graph import run_diagnosis
    import base64

    photo = (_FIXTURES_DIR / "non-animal-diagram-flowchart.png").read_bytes()
    result = run_diagnosis({}, image_base64=base64.b64encode(photo).decode(), species="GOAT")

    assert result["diagnosis"] == "invalid_image"
    assert result["recommended_action"] == "retry_upload"
    assert result["confidence"] == 0.0
