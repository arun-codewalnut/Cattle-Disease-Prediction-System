from pathlib import Path

from app.models.species_gate import is_animal_photo

_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _sample_species_photo(images_dir: str, folder: str) -> bytes:
    path = next((Path(__file__).resolve().parents[1] / "data" / images_dir / folder).glob("*.jpg"), None)
    if path is None:
        return None
    return path.read_bytes()


def test_real_non_animal_photos_are_rejected():
    for fixture in ("non-animal-table.jpg", "non-animal-car.jpg", "non-animal-text-screenshot.png"):
        photo = (_FIXTURES_DIR / fixture).read_bytes()
        assert is_animal_photo(photo) is False, f"{fixture} was incorrectly treated as an animal photo"


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
    assert is_animal_photo(photo) is True


def test_real_cat_photo_passes():
    photo = _sample_species_photo("cat-images", "healthy")
    if photo is None:
        import pytest

        pytest.skip("no local ml-service/data/cat-images — see its SOURCE.md")
    assert is_animal_photo(photo) is True


def test_real_dog_photo_passes():
    photo = _sample_species_photo("dog-images", "mange")
    if photo is None:
        import pytest

        pytest.skip("no local ml-service/data/dog-images — see its SOURCE.md")
    assert is_animal_photo(photo) is True


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
