import base64
from pathlib import Path
from types import SimpleNamespace

import app.agent.graph as graph_module
import app.models.cat_image_model as cat_image_model_module
import app.models.dog_image_model as dog_image_model_module
import app.models.goat_image_model as goat_image_model_module
import app.models.image_model as image_model_module
import app.models.sheep_symptom_model as sheep_symptom_model_module
import pytest
from app.agent.graph import run_diagnosis
from app.errors import ApiError

CONFIDENT_SYMPTOMS = {
    "fever": True,
    "mouth_lesions": True,
    "excessive_salivation": True,
    "lameness": True,
    "appetite_loss": True,
}


def test_explain_falls_back_to_template_when_llm_unavailable():
    # conftest.py's autouse fixture makes get_llm() raise by default — this is the honest
    # "no Ollama running" state of this environment, exercised without any extra mocking.
    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["diagnosis"] != "uncertain"
    # The template names the diagnosis and the signs behind it, and states no percentage —
    # the heading already carries the one required confidence figure (docs/DISCLAIMER.md,
    # docs/specs/species-mismatch-and-actionable-results.md).
    assert result["diagnosis"] in result["explanation"]
    assert "strongest signs were" in result["explanation"]
    assert "%" not in result["explanation"]
    # Feature keys are humanised, never shown raw.
    assert "mouth_lesions" not in result["explanation"]
    assert "mouth lesions" in result["explanation"]


def test_explain_uses_llm_output_when_available(monkeypatch):
    fake_response = SimpleNamespace(content="The cow likely has FMD based on the classic symptom triad.")

    class FakeLLM:
        def invoke(self, messages):
            return fake_response

    monkeypatch.setattr(graph_module, "get_llm", lambda: FakeLLM())

    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["explanation"] == fake_response.content


def test_explain_llm_failure_mid_call_still_falls_back(monkeypatch):
    class BrokenLLM:
        def invoke(self, messages):
            raise TimeoutError("simulated LLM timeout")

    monkeypatch.setattr(graph_module, "get_llm", lambda: BrokenLLM())

    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["diagnosis"] in result["explanation"]
    assert result["diagnosis"] != "uncertain"


def test_uncertain_diagnosis_never_calls_the_llm(monkeypatch):
    calls = []
    monkeypatch.setattr(graph_module, "get_llm", lambda: calls.append("called"))

    result = run_diagnosis({})

    assert result["diagnosis"] == "uncertain"
    assert calls == []


# M9: the real image_model.pt artifact and cattle-images dataset are both gitignored (large,
# unverified-license real photos), so CI won't have them — tests needing a real confident
# image prediction skip gracefully there. See docs/specs/M9-cattle-image-classifier.md.
_IMAGE_MODEL_PATH = image_model_module.DEFAULT_MODEL_PATH
_CATTLE_IMAGES_DIR = Path(__file__).resolve().parents[1] / "data" / "cattle-images"
_HAS_TRAINED_IMAGE_MODEL = _IMAGE_MODEL_PATH.exists()


def _sample_image_base64(folder: str) -> str:
    sample = next((_CATTLE_IMAGES_DIR / folder).glob("*.jpg"))
    return base64.b64encode(sample.read_bytes()).decode()


@pytest.mark.skipif(not _HAS_TRAINED_IMAGE_MODEL, reason="no local ml-service/models/image_model.pt")
def test_image_base64_produces_a_real_diagnosis_per_class():
    for folder, expected in [
        ("healthy", "Healthy"),
        ("lumpy", "Lumpy Skin Disease"),
        ("foot-and-mouth", "Foot and Mouth Disease"),
    ]:
        result = run_diagnosis({}, image_base64=_sample_image_base64(folder))
        assert result["diagnosis"] == expected
        assert result["sources"] == [] or isinstance(result["sources"], list)


@pytest.mark.skipif(not _HAS_TRAINED_IMAGE_MODEL, reason="no local ml-service/models/image_model.pt")
def test_image_diagnosis_uses_the_real_llm_rag_explain_path(monkeypatch):
    # Unlike the M8 placeholder, a real image diagnosis now goes through the same explain
    # path as symptoms — get_llm() gets called, not skipped.
    calls = []

    class FakeLLM:
        def invoke(self, messages):
            calls.append("called")
            return SimpleNamespace(content="Grounded explanation.")

    monkeypatch.setattr(graph_module, "get_llm", lambda: FakeLLM())

    result = run_diagnosis({}, image_base64=_sample_image_base64("lumpy"))

    assert calls == ["called"]
    assert result["explanation"] == "Grounded explanation."


@pytest.mark.skipif(not _HAS_TRAINED_IMAGE_MODEL, reason="no local ml-service/models/image_model.pt")
def test_image_diagnosis_still_escalates_for_reportable_disease():
    result = run_diagnosis({}, image_base64=_sample_image_base64("lumpy"))

    assert result["diagnosis"] == "Lumpy Skin Disease"
    assert result["recommended_action"] == "escalate_to_vet"


# M13/M14 follow-up: Cat/Dog each have their own real, trained IMAGE model — same
# gitignored-artifact-so-skip-in-CI reasoning as the cattle model above. Species picks which
# model predict_image_node calls; see app.agent.graph._IMAGE_MODEL_BY_SPECIES.
_CAT_IMAGE_MODEL_PATH = cat_image_model_module.DEFAULT_MODEL_PATH
_CAT_IMAGES_DIR = Path(__file__).resolve().parents[1] / "data" / "cat-images"
_HAS_TRAINED_CAT_IMAGE_MODEL = _CAT_IMAGE_MODEL_PATH.exists()

_DOG_IMAGE_MODEL_PATH = dog_image_model_module.DEFAULT_MODEL_PATH
_DOG_IMAGES_DIR = Path(__file__).resolve().parents[1] / "data" / "dog-images"
_HAS_TRAINED_DOG_IMAGE_MODEL = _DOG_IMAGE_MODEL_PATH.exists()

# M16: Goat gets its own real, trained IMAGE model too — same gitignored-artifact reasoning.
_GOAT_IMAGE_MODEL_PATH = goat_image_model_module.DEFAULT_MODEL_PATH
_GOAT_IMAGES_DIR = Path(__file__).resolve().parents[1] / "data" / "goat-images"
_HAS_TRAINED_GOAT_IMAGE_MODEL = _GOAT_IMAGE_MODEL_PATH.exists()

# M12 follow-up: Sheep has its own real, trained SYMPTOM model (unlike Cat/Dog above, which
# are image-only) — see app.agent.graph._SYMPTOM_MODEL_BY_SPECIES.
_SHEEP_SYMPTOM_MODEL_PATH = sheep_symptom_model_module.DEFAULT_MODEL_PATH
_HAS_TRAINED_SHEEP_SYMPTOM_MODEL = _SHEEP_SYMPTOM_MODEL_PATH.exists()


def _species_image_files(images_dir: Path, folder: str) -> list[Path]:
    # M16: goat-images ships .jpeg, not .jpg (cat/dog's convention) — glob every extension the
    # trained models actually accept (app.models.image_model's PREPROCESS pipeline) rather than
    # assume one.
    return sorted(
        f for f in (images_dir / folder).iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png")
    )


def _sample_species_image_base64(images_dir: Path, folder: str) -> str:
    sample = _species_image_files(images_dir, folder)[0]
    return base64.b64encode(sample.read_bytes()).decode()


def _sample_species_images_base64(images_dir: Path, folder: str, n: int = 10) -> list[str]:
    # random.sample (fixed seed), not "first N by directory order" — a directory listing can
    # cluster same-shoot/similarly-hard images together, which made an earlier version of this
    # test flaky on a real, correctly-behaving model. A seeded random spread is a fairer,
    # still-reproducible sample of the class.
    import random

    all_files = _species_image_files(images_dir, folder)
    samples = random.Random(42).sample(all_files, min(n, len(all_files)))
    return [base64.b64encode(s.read_bytes()).decode() for s in samples]


@pytest.mark.skipif(not _HAS_TRAINED_CAT_IMAGE_MODEL, reason="no local ml-service/models/cat_image_model.pt")
def test_cat_species_routes_to_the_cat_model_per_class():
    # Cat's real per-class F1 is 0.77-0.86, not 1.0 — asserting a single arbitrary sample per
    # class would occasionally fail on a genuinely-correct model just from picking an unlucky
    # image. Requiring half of 10 random samples correct is comfortably below the model's real
    # recall (77-86%) while still failing on genuine breakage (~25% expected from 4-way chance).
    for folder, expected in [
        ("flea-allergy", "Flea Allergy"),
        ("healthy", "Healthy"),
        ("ringworm", "Ringworm"),
        ("scabies", "Scabies"),
    ]:
        images = _sample_species_images_base64(_CAT_IMAGES_DIR, folder)
        diagnoses = [run_diagnosis({}, image_base64=img, species="CAT")["diagnosis"] for img in images]
        correct = sum(1 for d in diagnoses if d == expected)
        assert correct >= 5, f"{folder}: only {correct}/10 correctly diagnosed as {expected}, got {diagnoses}"


@pytest.mark.skipif(not _HAS_TRAINED_DOG_IMAGE_MODEL, reason="no local ml-service/models/dog_image_model.pt")
def test_dog_species_routes_to_the_dog_model():
    # M16 follow-up: the dog model was retrained on a new dataset (70.5% acc, 0.683 macro F1 —
    # see docs/specs/M14-dog-disease-detection.md's "Follow-up: Dog image model v2" section).
    # Only asserting the two classes with strong measured recall (Healthy ~96%, Fungal
    # Infection ~70%), not all 4 — Bacterial Dermatosis's recall (~42%) is too close to chance
    # for a tight per-sample threshold to be an honest signal of breakage vs. real model noise.
    for folder, expected, min_correct in [
        ("healthy", "Healthy", 8),
        ("fungal-infection", "Fungal Infection", 5),
    ]:
        images = _sample_species_images_base64(_DOG_IMAGES_DIR, folder)
        diagnoses = [run_diagnosis({}, image_base64=img, species="DOG")["diagnosis"] for img in images]
        correct = sum(1 for d in diagnoses if d == expected)
        assert correct >= min_correct, f"{folder}: only {correct}/10 correctly diagnosed as {expected}, got {diagnoses}"


@pytest.mark.skipif(not _HAS_TRAINED_GOAT_IMAGE_MODEL, reason="no local ml-service/models/goat_image_model.pt")
def test_goat_species_routes_to_the_goat_model():
    # Goat's model is binary (Healthy/Unhealthy, 80.1% acc, 0.800 macro F1 — see
    # docs/specs/M16-goat-disease-detection.md) — both classes have comparable, decent recall
    # (per-class F1 0.786/0.814), so both get a real assertion, same bar as Cat's per-class test.
    for folder, expected in [("healthy", "Healthy"), ("unhealthy", "Unhealthy")]:
        images = _sample_species_images_base64(_GOAT_IMAGES_DIR, folder)
        diagnoses = [run_diagnosis({}, image_base64=img, species="GOAT")["diagnosis"] for img in images]
        correct = sum(1 for d in diagnoses if d == expected)
        assert correct >= 5, f"{folder}: only {correct}/10 correctly diagnosed as {expected}, got {diagnoses}"


@pytest.mark.skipif(
    not (_HAS_TRAINED_CAT_IMAGE_MODEL and _HAS_TRAINED_DOG_IMAGE_MODEL),
    reason="no local ml-service/models/{cat,dog}_image_model.pt",
)
def test_unrecognized_species_falls_back_to_the_cattle_model():
    # Sheep isn't in _IMAGE_MODEL_BY_SPECIES (only symptom routing is species-aware for it —
    # see test_sheep_species_routes_symptoms_to_the_sheep_model below), so COW/SHEEP, or no
    # species at all, must all still hit the cattle image model unchanged.
    result = run_diagnosis({}, image_base64=_sample_image_base64("healthy"), species="SHEEP")
    assert result["diagnosis"] == "Healthy"


@pytest.mark.skipif(
    not _HAS_TRAINED_SHEEP_SYMPTOM_MODEL, reason="no local ml-service/models/sheep_symptom_model.pkl"
)
def test_sheep_species_routes_symptoms_to_the_sheep_model():
    # SHEEP on the *symptom* path must hit sheep_symptom_model, not the cattle model — the
    # two use entirely different feature vocabularies (see data/sheep-symptoms/SOURCE.md), so
    # this also implicitly checks unknown-to-that-model keys (cattle's "fever" etc.) don't
    # leak through: an all-PPR-symptoms case should come back positive regardless.
    all_present = {f: True for f in sheep_symptom_model_module.FEATURES}
    result = run_diagnosis(all_present, species="SHEEP")
    assert result["diagnosis"] == "PPR (Peste des Petits Ruminants)"
    assert result["recommended_action"] == "escalate_to_vet"


@pytest.mark.skipif(
    not _HAS_TRAINED_SHEEP_SYMPTOM_MODEL, reason="no local ml-service/models/sheep_symptom_model.pkl"
)
def test_sheep_symptoms_still_use_the_cattle_model_for_other_species():
    # Same symptom dict, no species — must land on the cattle model, not sheep's, since the
    # cattle CONFIDENT_SYMPTOMS fixture uses cattle-only feature names sheep_symptom_model
    # wouldn't even recognize.
    result = run_diagnosis(CONFIDENT_SYMPTOMS)
    assert result["diagnosis"] == "Foot and Mouth Disease"


def test_image_bytes_that_arent_a_real_image_degrade_to_uncertain():
    # Valid base64, but not a decodable image — app/models/image_model.py's own PIL-decode
    # failure path, distinct from _fetch_image_bytes's "couldn't even get bytes" cases below.
    image_base64 = base64.b64encode(b"not a real image, just arbitrary bytes").decode()

    result = run_diagnosis({}, image_base64=image_base64)

    assert result["diagnosis"] == "uncertain"
    assert result["recommended_action"] == "consult_vet"
    # M15: the "uncertain" explanation must talk about the photo, not symptoms, when this
    # came from the image path — it used to always say "not enough symptom information,"
    # which made no sense for a photo submission.
    assert "photo" in result["explanation"].lower()
    assert "symptom" not in result["explanation"].lower()


_FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _fixture_image_base64(name: str) -> str:
    return base64.b64encode((_FIXTURES_DIR / name).read_bytes()).decode()


@pytest.mark.parametrize("species", [None, "COW", "SHEEP", "CAT", "DOG", "GOAT"])
def test_non_animal_photo_is_rejected_as_invalid_image_for_every_species(species):
    # M15: a real photo that isn't an animal at all must never reach any species-specific
    # disease model, regardless of which species was selected — the gate runs before the
    # _IMAGE_MODEL_BY_SPECIES lookup.
    result = run_diagnosis({}, image_base64=_fixture_image_base64("non-animal-table.jpg"), species=species)

    assert result["diagnosis"] == "invalid_image"
    assert result["confidence"] == 0.0
    assert result["recommended_action"] == "retry_upload"
    assert "animal" in result["explanation"].lower()
    assert result["precautions"] == []
    assert result["next_steps"] == []


def test_invalid_image_never_calls_the_llm_or_retrieval(monkeypatch):
    calls = []
    monkeypatch.setattr(graph_module, "get_llm", lambda: calls.append("llm"))
    monkeypatch.setattr(graph_module, "retrieve", lambda *a, **k: calls.append("retrieve"))

    result = run_diagnosis({}, image_base64=_fixture_image_base64("non-animal-car.jpg"))

    assert result["diagnosis"] == "invalid_image"
    assert calls == []


# A tiny real 1x1 PNG, already base64-encoded — genuinely decodable, so tests using it
# exercise the "model missing" path specifically, not the "not a real image" decode-failure
# path tested above.
_VALID_1X1_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def test_missing_image_model_returns_structured_error(monkeypatch, tmp_path):
    # Always runs, everywhere — the actual behavior CI sees, since image_model.pt is
    # gitignored and not committed.
    monkeypatch.setattr(image_model_module, "DEFAULT_MODEL_PATH", tmp_path / "does-not-exist.pt")

    with pytest.raises(ApiError) as exc_info:
        run_diagnosis({}, image_base64=_VALID_1X1_PNG_BASE64)

    assert exc_info.value.code == "MODEL_NOT_TRAINED"


def test_missing_cat_image_model_returns_structured_error(monkeypatch, tmp_path):
    monkeypatch.setattr(cat_image_model_module, "DEFAULT_MODEL_PATH", tmp_path / "does-not-exist.pt")

    with pytest.raises(ApiError) as exc_info:
        run_diagnosis({}, image_base64=_VALID_1X1_PNG_BASE64, species="CAT")

    assert exc_info.value.code == "MODEL_NOT_TRAINED"


def test_missing_dog_image_model_returns_structured_error(monkeypatch, tmp_path):
    monkeypatch.setattr(dog_image_model_module, "DEFAULT_MODEL_PATH", tmp_path / "does-not-exist.pt")

    with pytest.raises(ApiError) as exc_info:
        run_diagnosis({}, image_base64=_VALID_1X1_PNG_BASE64, species="DOG")

    assert exc_info.value.code == "MODEL_NOT_TRAINED"


def test_missing_goat_image_model_returns_structured_error(monkeypatch, tmp_path):
    monkeypatch.setattr(goat_image_model_module, "DEFAULT_MODEL_PATH", tmp_path / "does-not-exist.pt")

    with pytest.raises(ApiError) as exc_info:
        run_diagnosis({}, image_base64=_VALID_1X1_PNG_BASE64, species="GOAT")

    assert exc_info.value.code == "MODEL_NOT_TRAINED"


def test_invalid_image_base64_degrades_to_uncertain_instead_of_failing():
    result = run_diagnosis({}, image_base64="not valid base64!!!")

    assert result["diagnosis"] == "uncertain"
    assert result["recommended_action"] == "consult_vet"


def test_unreachable_image_url_degrades_to_uncertain_instead_of_failing():
    result = run_diagnosis({}, image_url="http://127.0.0.1:1/does-not-resolve.jpg")

    assert result["diagnosis"] == "uncertain"
    assert result["recommended_action"] == "consult_vet"


def test_recommended_action_still_escalates_for_reportable_disease():
    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["diagnosis"] == "Foot and Mouth Disease"
    assert result["recommended_action"] == "escalate_to_vet"


def test_sources_populated_when_llm_and_retrieval_both_succeed(monkeypatch):
    # This used to need chromadb, and therefore Docker. Retrieval reads the checked-in
    # markdown directly now (docs/specs/remove-databases.md), so it runs natively.
    fake_response = SimpleNamespace(content="Grounded explanation using the reference material.")
    monkeypatch.setattr(graph_module, "get_llm", lambda: SimpleNamespace(invoke=lambda messages: fake_response))

    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["explanation"] == fake_response.content
    # Exact lookup, so this is now stricter than it could be under similarity search: the
    # diagnosis maps to exactly one document and no thematically-similar neighbour can be
    # dragged in with it.
    assert result["sources"] == ["foot-and-mouth-disease"]


def test_sources_empty_when_llm_falls_back_to_template():
    # Default autouse fixture makes get_llm() raise — explanation falls back to the
    # template, which doesn't cite anything, so sources must not claim retrieval was used.
    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["sources"] == []


def test_retrieval_failure_does_not_block_diagnosis(monkeypatch):
    def _broken_retrieve(query, k=3):
        raise RuntimeError("simulated Chroma failure")

    monkeypatch.setattr(graph_module, "retrieve", _broken_retrieve)

    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["diagnosis"] == "Foot and Mouth Disease"
    assert result["sources"] == []


def test_uncertain_diagnosis_never_calls_retrieval(monkeypatch):
    calls = []
    monkeypatch.setattr(graph_module, "retrieve", lambda query, k=3: calls.append(query))

    result = run_diagnosis({})

    assert result["diagnosis"] == "uncertain"
    assert calls == []


def test_uncertain_diagnosis_gets_hardcoded_precautions():
    # "uncertain" isn't a disease, so get_precautions() short-circuits before it looks for
    # a reference document at all (see app/rag/retrieval.py) — this guidance is hardcoded,
    # unlike the real-disease precautions read from markdown in test_rag_retrieval.py.
    result = run_diagnosis({})

    assert result["diagnosis"] == "uncertain"
    assert result["precautions"] == ["Keep monitoring the animal closely for any new or worsening symptoms."]
    assert result["next_steps"] == [
        "Provide more symptom details for a more confident prediction, or consult a vet directly."
    ]


def test_precautions_lookup_failure_does_not_block_diagnosis(monkeypatch):
    def _broken_get_precautions(diagnosis, persist_dir=None):
        raise RuntimeError("simulated Chroma failure")

    monkeypatch.setattr(graph_module, "get_precautions", _broken_get_precautions)

    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["diagnosis"] == "Foot and Mouth Disease"
    assert result["precautions"] == []
    assert result["next_steps"] == []
