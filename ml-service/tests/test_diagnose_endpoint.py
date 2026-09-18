import base64
from pathlib import Path

import app.models.symptom_model as symptom_model_module
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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


def test_image_base64_returns_placeholder_diagnosis_not_501() -> None:
    image_base64 = base64.b64encode(b"a fake photo for the placeholder pipeline").decode()

    response = client.post(
        "/agent/diagnose", json={"symptoms": {}, "image_base64": image_base64}
    )
    body = response.json()

    assert response.status_code == 200
    assert body["diagnosis"] in ("Healthy", "Lumpy Skin Disease", "Mastitis")
    assert body["confidence"] == 0.5
    assert "placeholder" in body["explanation"].lower()
    assert body["sources"] == []


def test_missing_model_returns_structured_error(monkeypatch, tmp_path: Path) -> None:
    # a fresh, never-before-seen path guarantees a cache miss in symptom_model's artifact
    # cache, so this hits the real FileNotFoundError -> ApiError path
    monkeypatch.setattr(symptom_model_module, "DEFAULT_MODEL_PATH", tmp_path / "does-not-exist.pkl")

    response = client.post("/agent/diagnose", json={"symptoms": {"fever": True}})
    body = response.json()

    assert response.status_code == 503
    assert body["code"] == "MODEL_NOT_TRAINED"
