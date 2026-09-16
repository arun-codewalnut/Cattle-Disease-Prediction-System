from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.agent.graph import run_diagnosis

router = APIRouter()


class DiagnoseRequest(BaseModel):
    symptoms: dict[str, Any]
    image_url: str | None = None


class DiagnoseResponse(BaseModel):
    diagnosis: str
    confidence: float
    explanation: str
    recommended_action: str
    sources: list[str]


@router.post("/agent/diagnose", response_model=DiagnoseResponse)
def diagnose(payload: DiagnoseRequest, request: Request) -> DiagnoseResponse:
    result = run_diagnosis(payload.symptoms, payload.image_url)
    return DiagnoseResponse(**result)
