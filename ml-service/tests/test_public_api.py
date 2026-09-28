"""The public API the frontend calls — POST /api/diagnoses and /api/diagnoses/image.

Ported from the Java backend's DiagnosisServiceTest / DiagnosisControllerTest when that
service was merged in here (docs/specs/merge-backend-into-ml-service.md): every case those
covered is here, with the agent faked the way they mocked MlServiceClient, plus the cases the
merge itself introduced (CORS, error passthrough, request-size cap). The last few tests run
the real, committed models end to end.
"""
from __future__ import annotations

import re
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.api.diagnoses as diagnoses_module
from app.errors import ApiError
from app.main import app

client = TestClient(app, raise_server_exceptions=False)

_JPEG = b"\xff\xd8\xff\xe0fake-jpeg-bytes"


def _ml_result(diagnosis: str = "Healthy", **overrides: Any) -> dict[str, Any]:
    result = {
        "diagnosis": diagnosis,
        "confidence": 0.9,
        "explanation": "x",
        "recommended_action": "monitor",
        "sources": ["some-doc.md"],
        "precautions": [],
        "next_steps": [],
    }
    result.update(overrides)
    return result


@pytest.fixture
def fake_agent(monkeypatch):
    """Replaces run_diagnosis. `calls` records every invocation; `results` is consumed in
    order (the last one repeats); an Exception in it is raised instead."""

    class Fake:
        def __init__(self):
            self.calls: list[dict[str, Any]] = []
            self.results: list[Any] = [_ml_result()]

        def __call__(self, symptoms, image_url=None, image_base64=None, species=None, model_path=None):
            self.calls.append({"symptoms": symptoms, "image_base64": image_base64, "species": species})
            result = self.results[min(len(self.calls), len(self.results)) - 1]
            if isinstance(result, Exception):
                raise result
            return result

    fake = Fake()
    monkeypatch.setattr(diagnoses_module, "run_diagnosis", fake)
    return fake


def _post_images(species: str | None = "COW", images: list[tuple[str, bytes, str]] | None = None, **kwargs):
    files = [("images", img) for img in (images if images is not None else [("cow.jpg", _JPEG, "image/jpeg")])]
    data = {"species": species} if species is not None else {}
    return client.post("/api/diagnoses/image", data=data, files=files or None, **kwargs)


# --- POST /api/diagnoses (symptoms) -------------------------------------------------------


def test_submit_symptoms_success_returns_diagnosis(fake_agent):
    fake_agent.results = [
        _ml_result(
            "Foot and Mouth Disease",
            confidence=0.81,
            recommended_action="escalate_to_vet",
            precautions=["Isolate the animal."],
            next_steps=["Contact your vet immediately."],
        )
    ]

    response = client.post("/api/diagnoses", json={"species": "COW", "symptoms": {"fever": True}})
    body = response.json()

    assert response.status_code == 201
    assert body["species"] == "COW"
    assert body["diagnosis"] == "Foot and Mouth Disease"
    assert body["confidence"] == 0.81
    assert body["recommendedAction"] == "escalate_to_vet"
    assert body["precautions"] == ["Isolate the animal."]
    assert body["nextSteps"] == ["Contact your vet immediately."]
    assert fake_agent.calls == [{"symptoms": {"fever": True}, "image_base64": None, "species": "COW"}]


def test_submit_symptoms_response_has_exactly_the_old_backend_fields(fake_agent):
    body = client.post("/api/diagnoses", json={"species": "COW", "symptoms": {}}).json()

    assert list(body) == [
        "species", "diagnosis", "confidence", "explanation",
        "recommendedAction", "precautions", "nextSteps", "createdAt",
    ]
    assert "sources" not in body
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(\.\d+)?Z", body["createdAt"])


def test_submit_symptoms_returns_the_requested_species(fake_agent):
    fake_agent.results = [_ml_result("PPR (Peste des Petits Ruminants)")]

    body = client.post("/api/diagnoses", json={"species": "SHEEP", "symptoms": {}}).json()

    assert body["species"] == "SHEEP"
    assert body["diagnosis"] == "PPR (Peste des Petits Ruminants)"
    assert fake_agent.calls[0]["species"] == "SHEEP"


def test_submit_symptoms_accepts_buffalo_and_forwards_it(fake_agent):
    # docs/specs/buffalo-symptoms-cow-model.md — the graph routes it to the cattle model.
    body = client.post("/api/diagnoses", json={"species": "BUFFALO", "symptoms": {"fever": True}}).json()

    assert body["species"] == "BUFFALO"
    assert fake_agent.calls[0]["species"] == "BUFFALO"


@pytest.mark.parametrize("species", ["CAT", "DOG"])
def test_submit_symptoms_image_only_species_rejected_before_model_call(fake_agent, species):
    response = client.post("/api/diagnoses", json={"species": species, "symptoms": {}})

    assert response.status_code == 400
    assert response.json() == {
        "code": "DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES",
        "message": f"Symptom-based diagnosis isn't available for species {species}.",
        "details": None,
    }
    assert fake_agent.calls == []


def test_submit_symptoms_agent_error_surfaces_with_its_own_code(fake_agent):
    # Replaces the Java ML_SERVICE_ERROR / ML_SERVICE_UNAVAILABLE cases: there's no network hop
    # any more, so the agent's own error reaches the caller unwrapped.
    fake_agent.results = [ApiError("MODEL_NOT_TRAINED", "The symptom_model hasn't been trained yet.", status_code=503)]

    response = client.post("/api/diagnoses", json={"species": "COW", "symptoms": {}})

    assert response.status_code == 503
    assert response.json() == {
        "code": "MODEL_NOT_TRAINED",
        "message": "The symptom_model hasn't been trained yet.",
        "details": None,
    }


def test_submit_symptoms_missing_species_returns_validation_failed(fake_agent):
    response = client.post("/api/diagnoses", json={"symptoms": {}})

    assert response.status_code == 400
    assert response.json() == {
        "code": "VALIDATION_FAILED",
        "message": "Request failed validation.",
        "details": {"species": "must not be null"},
    }


def test_submit_symptoms_all_missing_fields_are_listed(fake_agent):
    response = client.post("/api/diagnoses", json={"species": None})

    assert response.status_code == 400
    assert response.json()["details"] == {"species": "must not be null", "symptoms": "must not be null"}


@pytest.mark.parametrize(
    "payload",
    [
        {"species": "LLAMA", "symptoms": {}},
        {"species": "cow", "symptoms": {}},  # case-sensitive, like Jackson's enum binding
        {"species": ["COW"], "symptoms": {}},
        {"species": "COW", "symptoms": ["fever"]},
        {"species": "LLAMA"},  # a type error wins over a missing field
    ],
)
def test_submit_symptoms_invalid_values_return_invalid_request_body(fake_agent, payload):
    response = client.post("/api/diagnoses", json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST_BODY"
    assert fake_agent.calls == []


@pytest.mark.parametrize(
    "content, content_type",
    [
        ("{not json", "application/json"),
        ("[1, 2]", "application/json"),
        ("", "application/json"),
        ('{"species": "COW", "symptoms": {}}', "text/plain"),
    ],
)
def test_submit_symptoms_malformed_body_returns_invalid_request_body(fake_agent, content, content_type):
    response = client.post("/api/diagnoses", content=content, headers={"Content-Type": content_type})

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST_BODY"


def test_submit_symptoms_ignores_unknown_fields(fake_agent):
    response = client.post("/api/diagnoses", json={"species": "COW", "symptoms": {}, "tagNumber": "A1"})

    assert response.status_code == 201


# --- POST /api/diagnoses/image (photos) ---------------------------------------------------


def test_submit_image_success_encodes_as_base64_and_sends_empty_symptoms(fake_agent):
    fake_agent.results = [_ml_result("Lumpy Skin Disease", recommended_action="escalate_to_vet")]

    response = _post_images("COW")
    body = response.json()

    assert response.status_code == 201
    assert len(body["results"]) == 1
    assert body["results"][0]["diagnosis"] == "Lumpy Skin Disease"
    assert body["results"][0]["recommendedAction"] == "escalate_to_vet"
    assert body["diagnosesAgree"] is True  # a single photo always agrees with itself
    assert fake_agent.calls == [
        {"symptoms": {}, "image_base64": "/9j/4GZha2UtanBlZy1ieXRlcw==", "species": "COW"}
    ]


def test_submit_image_species_mismatch_is_passed_through_as_a_non_diagnosis(fake_agent):
    fake_agent.results = [_ml_result("species_mismatch", confidence=0.0, recommended_action="retry_upload")]

    result = _post_images("COW").json()["results"][0]

    assert result["diagnosis"] == "species_mismatch"
    assert result["recommendedAction"] == "retry_upload"
    assert result["confidence"] == 0.0


def test_submit_image_multiple_photos_all_same_diagnosis_agree(fake_agent):
    fake_agent.results = [_ml_result("Healthy")]

    body = _post_images("COW", [("a.jpg", _JPEG, "image/jpeg")] * 3).json()

    assert len(body["results"]) == 3
    assert body["diagnosesAgree"] is True
    assert len(fake_agent.calls) == 3


def test_submit_image_multiple_photos_disagreeing_diagnoses_flag_disagreement(fake_agent):
    fake_agent.results = [_ml_result("Healthy"), _ml_result("Lumpy Skin Disease"), _ml_result("Healthy")]

    body = _post_images("COW", [("a.jpg", _JPEG, "image/jpeg")] * 3).json()

    assert len(body["results"]) == 3
    assert body["diagnosesAgree"] is False


@pytest.mark.parametrize("non_diagnosis", ["invalid_image", "species_mismatch"])
def test_submit_image_matching_diagnoses_plus_one_non_diagnosis_still_agree(fake_agent, non_diagnosis):
    fake_agent.results = [_ml_result("Lumpy Skin Disease"), _ml_result("Lumpy Skin Disease"), _ml_result(non_diagnosis)]

    body = _post_images("COW", [("a.jpg", _JPEG, "image/jpeg")] * 3).json()

    assert body["diagnosesAgree"] is True
    assert body["results"][2]["diagnosis"] == non_diagnosis


@pytest.mark.parametrize("count", [6, 7])
def test_submit_image_more_than_five_photos_rejected_before_model_call(fake_agent, count):
    response = _post_images("COW", [("a.jpg", _JPEG, "image/jpeg")] * count)

    assert response.status_code == 400
    assert response.json()["code"] == "TOO_MANY_IMAGES"
    assert response.json()["message"] == f"At most 5 images are accepted per submission, got {count}."
    assert fake_agent.calls == []


def test_submit_image_unsupported_type_rejected_before_model_call(fake_agent):
    response = _post_images("COW", [("a.jpg", _JPEG, "image/jpeg"), ("b.gif", b"GIF89a", "image/gif")])

    assert response.status_code == 400
    assert response.json()["code"] == "UNSUPPORTED_IMAGE_TYPE"
    assert "'image/gif'" in response.json()["message"]
    assert fake_agent.calls == []


def test_submit_image_too_large_rejected_before_model_call(fake_agent):
    too_big = b"\xff" * (5 * 1024 * 1024 + 1)

    response = _post_images("COW", [("big.jpg", too_big, "image/jpeg")])

    assert response.status_code == 400
    assert response.json() == {"code": "IMAGE_TOO_LARGE", "message": "Image exceeds the 5MB size limit.", "details": None}
    assert fake_agent.calls == []


def test_submit_image_several_normal_photos_over_5mb_total_are_accepted(fake_agent):
    # Deliberate difference from the Java backend, which capped the whole request at 5MB.
    photo = b"\xff" * (3 * 1024 * 1024)

    response = _post_images("COW", [("a.jpg", photo, "image/jpeg")] * 2)

    assert response.status_code == 201


def test_submit_image_request_over_the_size_cap_rejected_without_parsing(fake_agent):
    response = client.post(
        "/api/diagnoses/image",
        content=b"x",
        headers={"Content-Type": "multipart/form-data; boundary=abc", "Content-Length": str(27 * 1024 * 1024)},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "IMAGE_TOO_LARGE"


def test_submit_image_empty_file_rejected(fake_agent):
    response = _post_images("COW", [("empty.jpg", b"", "image/jpeg")])

    assert response.status_code == 400
    assert response.json()["code"] == "IMAGE_REQUIRED"


def test_submit_image_no_files_rejected(fake_agent):
    # A multipart request whose only file isn't under the `images` field.
    response = client.post(
        "/api/diagnoses/image", data={"species": "COW"}, files={"not-images": ("x.jpg", _JPEG, "image/jpeg")}
    )

    assert response.status_code == 400
    assert response.json()["code"] == "IMAGE_REQUIRED"


def test_submit_image_wrong_content_type_returns_clean_image_required_not_a_500(fake_agent):
    response = client.post(
        "/api/diagnoses/image", content="species=COW", headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    assert response.status_code == 400
    assert response.json()["code"] == "IMAGE_REQUIRED"


def test_submit_image_buffalo_rejected_before_model_call(fake_agent):
    # Symptoms only: the cattle photo model has never seen a buffalo.
    response = _post_images(species="BUFFALO")

    assert response.status_code == 400
    assert response.json() == {
        "code": "DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES",
        "message": "Image-based diagnosis isn't available for species BUFFALO.",
        "details": None,
    }
    assert fake_agent.calls == []


def test_submit_image_missing_species_form_field_returns_validation_failed(fake_agent):
    response = _post_images(None)

    assert response.status_code == 400
    assert response.json() == {
        "code": "VALIDATION_FAILED",
        "message": "Request failed validation.",
        "details": {"species": "must not be null"},
    }


def test_submit_image_invalid_species_value_returns_invalid_request_body(fake_agent):
    response = _post_images("LLAMA")

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_REQUEST_BODY"


def test_submit_image_species_whitespace_is_trimmed(fake_agent):
    # Spring's String-to-enum conversion trimmed form values.
    assert _post_images(" COW ").status_code == 201


@pytest.mark.parametrize("species, diagnosis", [("CAT", "Ringworm"), ("DOG", "Fungal Infection"), ("GOAT", "Unhealthy")])
def test_submit_image_image_only_species_succeed_and_forward_species(fake_agent, species, diagnosis):
    fake_agent.results = [_ml_result(diagnosis)]

    body = _post_images(species).json()

    assert body["results"][0]["species"] == species
    assert body["results"][0]["diagnosis"] == diagnosis
    assert fake_agent.calls[0]["species"] == species


def test_submit_image_png_is_accepted(fake_agent):
    assert _post_images("COW", [("a.png", b"\x89PNG\r\n", "image/png")]).status_code == 201


# --- Cross-cutting ------------------------------------------------------------------------


def test_correlation_id_is_echoed_back(fake_agent):
    response = client.post(
        "/api/diagnoses", json={"species": "COW", "symptoms": {}}, headers={"X-Correlation-Id": "abc-123"}
    )

    assert response.headers["x-correlation-id"] == "abc-123"


def test_correlation_id_is_generated_when_absent(fake_agent):
    response = client.post("/api/diagnoses", json={"species": "COW", "symptoms": {}})

    assert response.headers["x-correlation-id"]


def test_cors_preflight_allows_the_frontend_origin():
    response = client.options(
        "/api/diagnoses",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-correlation-id",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_rejects_an_unknown_origin():
    response = client.options(
        "/api/diagnoses",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )

    assert "access-control-allow-origin" not in response.headers


def test_unexpected_error_returns_internal_error_with_cors_headers(fake_agent):
    fake_agent.results = [RuntimeError("boom")]

    response = client.post(
        "/api/diagnoses", json={"species": "COW", "symptoms": {}}, headers={"Origin": "http://localhost:5173"}
    )

    assert response.status_code == 500
    assert response.json() == {"code": "INTERNAL_ERROR", "message": "boom", "details": None}
    # Without this the browser reports a CORS failure instead of the message.
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_unknown_path_returns_not_found_in_the_standard_shape():
    response = client.post("/api/animals", json={})

    assert response.status_code == 404
    assert response.json() == {"code": "NOT_FOUND", "message": "No endpoint exists at this path.", "details": None}


def test_old_spring_health_path_is_gone_and_health_still_works():
    assert client.get("/actuator/health").status_code == 404
    assert client.get("/health").json() == {"status": "ok"}


# --- Real models, end to end (the artifacts are committed) --------------------------------


def test_real_symptom_diagnosis_escalates_a_reportable_disease():
    response = client.post(
        "/api/diagnoses",
        json={
            "species": "COW",
            "symptoms": {"fever": True, "mouth_lesions": True, "excessive_salivation": True, "lameness": True},
        },
    )
    body = response.json()

    assert response.status_code == 201
    assert body["diagnosis"] == "Foot and Mouth Disease"
    assert body["recommendedAction"] == "escalate_to_vet"
    assert body["precautions"] and body["nextSteps"]


def test_real_sheep_symptom_diagnosis_routes_to_the_sheep_model():
    response = client.post("/api/diagnoses", json={"species": "SHEEP", "symptoms": {}})

    assert response.status_code == 201
    assert response.json()["species"] == "SHEEP"


def test_submit_symptoms_goat_is_accepted_and_forwarded(fake_agent):
    fake_agent.results = [_ml_result("PPR Negative")]

    response = client.post("/api/diagnoses", json={"species": "GOAT", "symptoms": {"temp": False}})

    assert response.status_code == 201
    assert response.json()["species"] == "GOAT"
    assert fake_agent.calls[0]["species"] == "GOAT"


def test_real_goat_symptom_diagnosis_screens_for_ppr_and_escalates():
    # The spec's example: the two signs that reliably mean PPR on this model.
    response = client.post(
        "/api/diagnoses", json={"species": "GOAT", "symptoms": {"nasal_discharge": True, "oral_nasal_lesion": True}}
    )
    body = response.json()

    assert response.status_code == 201
    assert body["species"] == "GOAT"
    assert body["diagnosis"] == "PPR (Peste des Petits Ruminants)"
    assert body["recommendedAction"] == "escalate_to_vet"
    assert body["precautions"] and body["nextSteps"]

    # Nothing ticked in the UI is every symptom sent as false (an empty {} is "no
    # information" and comes back uncertain instead).
    none_ticked = {k: False for k in ["temp", "nasal_discharge", "diarrhea", "difficult_breathing", "eye_discharge", "oral_nasal_lesion"]}
    negative = client.post("/api/diagnoses", json={"species": "GOAT", "symptoms": none_ticked}).json()
    assert negative["diagnosis"] == "PPR Negative"


def test_real_image_diagnosis_rejects_a_non_animal_picture():
    # A real, decodable 1x1 PNG — the M15 gate should refuse it rather than guess a disease.
    png_1x1 = bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010804000000b51c0c02"
        "0000000b4944415478da63fcff1f0003030200efa53a9c0000000049454e44ae426082"
    )

    response = _post_images("COW", [("dot.png", png_1x1, "image/png")])
    result = response.json()["results"][0]

    assert response.status_code == 201
    assert result["diagnosis"] == "invalid_image"
    assert result["recommendedAction"] == "retry_upload"
