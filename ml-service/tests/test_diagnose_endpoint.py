import base64
from pathlib import Path

import app.models.image_model as image_model_module
import app.models.symptom_model as symptom_model_module
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# M9: the cattle-images dataset is gitignored (large, unverified-license real photos) so CI
# won't have it — tests needing a real confident image prediction skip gracefully there rather
# than fail. The model artifact itself is committed now (docs/DECISIONS.md), so the flag needs
# the sample photos too; the "no model trained" case below monkeypatches the path and always
# runs. See docs/specs/M9-cattle-image-classifier.md.
_CATTLE_IMAGES_DIR = Path(__file__).resolve().parents[1] / "data" / "cattle-images"


def _has_sample_photos(images_dir: Path) -> bool:
    # The dataset folders themselves exist in git (each keeps a tracked SOURCE.md) — only the
    # photos are gitignored, so check for real image files, not just the directory.
    return any(f.suffix.lower() in (".jpg", ".jpeg", ".png") for f in images_dir.rglob("*"))


_HAS_TRAINED_IMAGE_MODEL = image_model_module.DEFAULT_MODEL_PATH.exists() and _has_sample_photos(_CATTLE_IMAGES_DIR)


def _sample_image_base64(folder: str) -> str:
    sample = next((_CATTLE_IMAGES_DIR / folder).glob("*.jpg"))
    return base64.b64encode(sample.read_bytes()).decode()


# A tiny real 1x1 PNG, already base64-encoded — genuinely decodable, so tests using it
# exercise the "model missing" path specifically, not image_model.py's separate "not a real
# image" decode-failure path.
_VALID_1X1_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def test_reportable_disease_always_escalates() -> None:
    response = client.post(
        "/agent/diagnose",
        json={
            "symptoms": {
                "fever": True,
                "mouth_lesions": True,
                "excessive_salivation": True,
                "lameness": True,
            }
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["diagnosis"] == "Foot and Mouth Disease"
    assert body["recommended_action"] == "escalate_to_vet"
    assert body["confidence"] >= 0.4
    assert "Foot and Mouth Disease" in body["explanation"]
    assert body["sources"] == []


def test_uncertain_recommends_consult_vet() -> None:
    response = client.post("/agent/diagnose", json={"symptoms": {}})
    body = response.json()

    assert response.status_code == 200
    assert body["diagnosis"] == "uncertain"
    assert body["confidence"] < 0.4
    assert body["recommended_action"] == "consult_vet"


def test_non_reportable_disease_recommends_consult_vet_not_escalate() -> None:
    response = client.post(
        "/agent/diagnose",
        json={"symptoms": {"milk_yield_drop": True, "udder_swelling": True, "fever": True}},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["diagnosis"] == "Mastitis"
    assert body["recommended_action"] == "consult_vet"


def test_healthy_recommends_monitor() -> None:
    all_false = {
        "fever": False, "appetite_loss": False, "nasal_discharge": False,
        "milk_yield_drop": False, "mouth_lesions": False, "lameness": False,
        "excessive_salivation": False, "skin_nodules": False, "udder_swelling": False,
        "coughing": False, "labored_breathing": False,
    }
    response = client.post("/agent/diagnose", json={"symptoms": all_false})
    body = response.json()

    assert response.status_code == 200
    assert body["diagnosis"] == "Healthy"
    assert body["recommended_action"] == "monitor"


@pytest.mark.skipif(not _HAS_TRAINED_IMAGE_MODEL, reason="no local image_model.pt or data/cattle-images/")
def test_image_base64_returns_real_diagnosis_via_llm_rag_path() -> None:
    image_base64 = _sample_image_base64("lumpy")

    response = client.post(
        "/agent/diagnose", json={"symptoms": {}, "image_base64": image_base64}
    )
    body = response.json()

    assert response.status_code == 200
    assert body["diagnosis"] == "Lumpy Skin Disease"
    assert body["recommended_action"] == "escalate_to_vet"
    # M9: real model now, so explanation goes through the same LLM/template path symptom
    # diagnoses use — no more "this is a placeholder" wording.
    assert "placeholder" not in body["explanation"].lower()


def test_image_bytes_that_arent_a_real_image_degrade_to_uncertain() -> None:
    image_base64 = base64.b64encode(b"not a real image, just arbitrary bytes").decode()

    response = client.post(
        "/agent/diagnose", json={"symptoms": {}, "image_base64": image_base64}
    )
    body = response.json()

    assert response.status_code == 200
    assert body["diagnosis"] == "uncertain"
    assert body["recommended_action"] == "consult_vet"


def test_missing_model_returns_structured_error(monkeypatch, tmp_path: Path) -> None:
    # a fresh, never-before-seen path guarantees a cache miss in symptom_model's artifact
    # cache, so this hits the real FileNotFoundError -> ApiError path
    monkeypatch.setattr(symptom_model_module, "DEFAULT_MODEL_PATH", tmp_path / "does-not-exist.pkl")

    response = client.post("/agent/diagnose", json={"symptoms": {"fever": True}})
    body = response.json()

    assert response.status_code == 503
    assert body["code"] == "MODEL_NOT_TRAINED"


def test_missing_image_model_returns_structured_error(monkeypatch, tmp_path: Path) -> None:
    # Always runs, everywhere (unlike the real-prediction test above) — the model path is
    # pointed somewhere empty, so this holds whether or not the committed artifact exists.
    # See docs/specs/M9-cattle-image-classifier.md.
    monkeypatch.setattr(image_model_module, "DEFAULT_MODEL_PATH", tmp_path / "does-not-exist.pt")

    response = client.post(
        "/agent/diagnose", json={"symptoms": {}, "image_base64": _VALID_1X1_PNG_BASE64}
    )
    body = response.json()

    assert response.status_code == 503
    assert body["code"] == "MODEL_NOT_TRAINED"
