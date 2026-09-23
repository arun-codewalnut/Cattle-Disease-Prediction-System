from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.agent.graph import run_diagnosis

router = APIRouter()


class DiagnoseRequest(BaseModel):
    symptoms: dict[str, Any]
    image_url: str | None = None
    image_base64: str | None = None
    # Only used to pick which trained image model runs (Cat/Dog get their own; everything
    # else falls back to the cattle model) — never forwarded to or used by the symptom path,
    # same species-agnostic behavior that's always applied there. See app/agent/graph.py.
    species: str | None = None


class DiagnoseResponse(BaseModel):
    diagnosis: str
    confidence: float
    explanation: str
    recommended_action: str
    sources: list[str]
    precautions: list[str]
    next_steps: list[str]
    # Set when an uploaded photo doesn't look like the selected species — advisory, the
    # diagnosis is still returned. See docs/specs/species-mismatch-and-actionable-results.md.
    species_warning: str | None = None


@router.post("/agent/diagnose", response_model=DiagnoseResponse)
def diagnose(payload: DiagnoseRequest, request: Request) -> DiagnoseResponse:
    result = run_diagnosis(payload.symptoms, payload.image_url, payload.image_base64, payload.species)
    return DiagnoseResponse(**result)
