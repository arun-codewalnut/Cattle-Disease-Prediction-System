"""Public diagnosis API the frontend calls — POST /api/diagnoses and /api/diagnoses/image.

This used to be the Java `backend` service, a stateless gateway that validated requests,
called POST /agent/diagnose over HTTP and reshaped the result. It now lives here and calls
the agent in-process. The contract (paths, status codes, camelCase fields, error codes) is
unchanged so the frontend didn't have to change — see docs/specs/merge-backend-into-ml-service.md
and docs/API_CONTRACTS.md.

Request bodies are parsed by hand rather than through Pydantic models, so each failure maps to
the exact error code the frontend already handles (FastAPI's default is a 422 with its own
shape).
"""
from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile

from app.agent.graph import run_diagnosis
from app.errors import ApiError

logger = logging.getLogger("ml_service.api")

router = APIRouter(prefix="/api")


class Species(str, Enum):
    """Which trained model runs. Never reorder — values are the wire format.

    BUFFALO was removed on 2026-09-22 and came back on 2026-09-28, symptoms only, using the
    cattle model as a labelled approximation — see docs/specs/buffalo-symptoms-cow-model.md."""

    COW = "COW"
    SHEEP = "SHEEP"
    CAT = "CAT"
    DOG = "DOG"
    GOAT = "GOAT"
    BUFFALO = "BUFFALO"


# Symptom diagnosis: Cow has the cattle model; Sheep and Goat share the PPR model (M12, and
# docs/specs/goat-ppr-symptom-screen.md); Buffalo borrows the cattle model as a labelled
# approximation (docs/specs/buffalo-symptoms-cow-model.md). Cat/Dog stay blocked — no usable
# symptom dataset exists for them, and the cattle model's disease list doesn't apply to a pet.
SYMPTOM_SUPPORTED_SPECIES = frozenset({Species.COW, Species.SHEEP, Species.GOAT, Species.BUFFALO})

# Photo diagnosis: Cow, plus the species with their own trained image model (M13/M14/M16), plus
# Sheep on the cattle model. Not Buffalo — the cattle photo model has never seen buffalo skin,
# so it's listed explicitly rather than derived from the symptom set.
IMAGE_SUPPORTED_SPECIES = frozenset({Species.COW, Species.SHEEP, Species.GOAT, Species.CAT, Species.DOG})

ALLOWED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png"})
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
MAX_IMAGES = 5
# Checked from Content-Length before the body is parsed, so an oversized upload is rejected
# without reading it. Room for five full-size photos plus multipart overhead — the Java
# backend capped the *whole request* at 5MB, which rejected two ordinary phone photos.
MAX_REQUEST_BYTES = MAX_IMAGES * MAX_IMAGE_SIZE_BYTES + 1024 * 1024

# Neither is a diagnosis, so neither can agree or disagree with one: a photo that isn't an
# animal (M15), and a photo that isn't the selected species.
NON_DIAGNOSES = frozenset({"invalid_image", "species_mismatch"})


class DiagnosisCaseResponse(BaseModel):
    species: Species
    diagnosis: str
    confidence: float
    explanation: str
    recommendedAction: str
    precautions: list[str]
    nextSteps: list[str]
    createdAt: str


class ImageDiagnosisBatchResponse(BaseModel):
    results: list[DiagnosisCaseResponse]
    diagnosesAgree: bool


def _invalid_body() -> ApiError:
    return ApiError("INVALID_REQUEST_BODY", "Request body is malformed or contains an invalid value.")


def _validation_failed(missing_fields: list[str]) -> ApiError:
    return ApiError(
        "VALIDATION_FAILED", "Request failed validation.", {field: "must not be null" for field in missing_fields}
    )


def _image_required(message: str = "An image file is required.") -> ApiError:
    return ApiError("IMAGE_REQUIRED", message)


def _to_case_response(species: Species, result: dict[str, Any]) -> dict[str, Any]:
    # `sources` is deliberately dropped — the frontend never received it from the old backend.
    return DiagnosisCaseResponse(
        species=species,
        diagnosis=result["diagnosis"],
        confidence=result["confidence"],
        explanation=result["explanation"],
        recommendedAction=result["recommended_action"],
        precautions=result["precautions"],
        nextSteps=result["next_steps"],
        createdAt=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    ).model_dump(mode="json")


def diagnoses_agree(diagnoses: list[str]) -> bool:
    """True when every real diagnosis is the same. One photo always agrees with itself, and
    invalid_image / species_mismatch results are ignored — 4 matching photos plus one
    accidental unrelated upload should still read as "agree"."""
    return len({d for d in diagnoses if d not in NON_DIAGNOSES}) <= 1


def diagnose_symptoms(species: Species, symptoms: dict[str, Any]) -> dict[str, Any]:
    if species not in SYMPTOM_SUPPORTED_SPECIES:
        raise ApiError(
            "DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES",
            f"Symptom-based diagnosis isn't available for species {species.value}.",
        )
    # species is forwarded so Sheep routes to its own trained symptom model.
    result = run_diagnosis(symptoms, None, None, species.value)
    return _to_case_response(species, result)


def diagnose_images(species: Species, images: list[tuple[str | None, bytes]]) -> dict[str, Any]:
    """`images` is (content_type, bytes) per uploaded photo. Everything is validated before any
    model runs; each photo is then diagnosed independently against the same model."""
    if not images:
        raise _image_required("At least one image file is required.")
    if len(images) > MAX_IMAGES:
        raise ApiError(
            "TOO_MANY_IMAGES", f"At most {MAX_IMAGES} images are accepted per submission, got {len(images)}."
        )
    for content_type, data in images:
        if not data:
            raise _image_required()
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise ApiError(
                "UNSUPPORTED_IMAGE_TYPE",
                f"Unsupported image type '{content_type}' — only JPEG and PNG are accepted.",
            )
        if len(data) > MAX_IMAGE_SIZE_BYTES:
            raise ApiError("IMAGE_TOO_LARGE", "Image exceeds the 5MB size limit.")

    if species not in IMAGE_SUPPORTED_SPECIES:
        raise ApiError(
            "DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES",
            f"Image-based diagnosis isn't available for species {species.value}.",
        )

    results = []
    for _, data in images:
        # No symptoms for a photo diagnosis — an empty dict, not None. species picks the
        # species' own image model (Cat/Dog/Goat), falling back to the cattle model.
        result = run_diagnosis({}, None, base64.b64encode(data).decode(), species.value)
        results.append(_to_case_response(species, result))

    return ImageDiagnosisBatchResponse(
        results=results, diagnosesAgree=diagnoses_agree([r["diagnosis"] for r in results])
    ).model_dump(mode="json")


def _parse_symptom_request(raw: bytes, content_type: str) -> tuple[Species, dict[str, Any]]:
    media_type = content_type.split(";")[0].strip().lower()
    if media_type != "application/json" and not media_type.endswith("+json"):
        raise _invalid_body()
    try:
        body = json.loads(raw)
    except ValueError:
        raise _invalid_body() from None
    if not isinstance(body, dict):
        raise _invalid_body()

    species_raw, symptoms = body.get("species"), body.get("symptoms")
    # Type errors first, then missing fields — the order Spring's Jackson-then-@Valid ran in.
    if species_raw is not None and (not isinstance(species_raw, str) or species_raw not in Species.__members__):
        raise _invalid_body()
    if symptoms is not None and not isinstance(symptoms, dict):
        raise _invalid_body()
    missing = [name for name, value in (("species", species_raw), ("symptoms", symptoms)) if value is None]
    if missing:
        raise _validation_failed(missing)
    return Species(species_raw), symptoms


_SYMPTOM_REQUEST_SCHEMA = {
    "required": True,
    "content": {
        "application/json": {
            "schema": {
                "type": "object",
                "required": ["species", "symptoms"],
                "properties": {
                    "species": {"type": "string", "enum": [s.value for s in Species]},
                    "symptoms": {"type": "object", "additionalProperties": True},
                },
            }
        }
    },
}

_IMAGE_REQUEST_SCHEMA = {
    "required": True,
    "content": {
        "multipart/form-data": {
            "schema": {
                "type": "object",
                "required": ["species", "images"],
                "properties": {
                    "species": {"type": "string", "enum": [s.value for s in Species]},
                    "images": {"type": "array", "items": {"type": "string", "format": "binary"}, "maxItems": MAX_IMAGES},
                },
            }
        }
    },
}


@router.post(
    "/diagnoses",
    status_code=201,
    response_model=DiagnosisCaseResponse,
    openapi_extra={"requestBody": _SYMPTOM_REQUEST_SCHEMA},
)
async def submit_symptoms(request: Request) -> JSONResponse:
    species, symptoms = _parse_symptom_request(await request.body(), request.headers.get("content-type", ""))
    logger.info("[%s] symptom diagnosis species=%s", request.state.correlation_id, species.value)
    # Inference is synchronous and can take a while — keep it off the event loop.
    result = await run_in_threadpool(diagnose_symptoms, species, symptoms)
    return JSONResponse(result, status_code=201)


@router.post(
    "/diagnoses/image",
    status_code=201,
    response_model=ImageDiagnosisBatchResponse,
    openapi_extra={"requestBody": _IMAGE_REQUEST_SCHEMA},
)
async def submit_image(request: Request) -> JSONResponse:
    # Some clients send a plain form (or nothing) when there's no file to attach.
    if not request.headers.get("content-type", "").lower().startswith("multipart/form-data"):
        raise _image_required()
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_REQUEST_BYTES:
        raise ApiError("IMAGE_TOO_LARGE", "Uploaded file exceeds the size limit.")

    try:
        # A generous parser cap, well above MAX_IMAGES, so 6+ photos still reach the clearer
        # TOO_MANY_IMAGES check below; Content-Length above already bounds the total size.
        form = await request.form(max_files=50, max_fields=100)
    except Exception:  # malformed multipart body, or more parts than we'd ever accept
        raise _image_required() from None

    try:
        species_raw = form.get("species")
        species_value = species_raw.strip() if isinstance(species_raw, str) else ""
        if not species_value:
            raise _validation_failed(["species"])
        if species_value not in Species.__members__:
            raise _invalid_body()
        species = Species(species_value)

        uploads = [part for part in form.getlist("images") if isinstance(part, UploadFile)]
        if not uploads:
            raise _image_required()
        images = [(upload.content_type, await upload.read()) for upload in uploads]
    finally:
        await form.close()

    logger.info(
        "[%s] image diagnosis species=%s photos=%d", request.state.correlation_id, species.value, len(images)
    )
    result = await run_in_threadpool(diagnose_images, species, images)
    return JSONResponse(result, status_code=201)
