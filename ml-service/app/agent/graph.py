"""
Agent wiring for /agent/diagnose.

See docs/specs/M2-wire-model-into-agent.md. This is deliberately a plain function, not a
LangGraph StateGraph yet — that's M5. `explanation` is a deterministic template, not
LLM-generated — RAG-grounded explanation is M6.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from app.errors import ApiError
from app.models.symptom_model import predict

# Diseases that must always escalate regardless of model confidence, per docs/DISCLAIMER.md.
# Deliberately a fixed, auditable list here rather than anything the model could drift on.
REPORTABLE_DISEASES = {"Foot and Mouth Disease", "Lumpy Skin Disease"}


def _recommended_action(diagnosis: str) -> str:
    if diagnosis in REPORTABLE_DISEASES:
        return "escalate_to_vet"
    if diagnosis == "uncertain":
        return "consult_vet"
    if diagnosis == "Healthy":
        return "monitor"
    return "consult_vet"


def _explanation(result: dict[str, Any]) -> str:
    if result["diagnosis"] == "uncertain":
        return (
            "Not enough symptom information was provided to make a confident prediction. "
            "Provide more symptom details or consult a vet directly."
        )

    top_feature_names = [f["feature"] for f in result["top_features"]]
    basis = f", based primarily on: {', '.join(top_feature_names)}" if top_feature_names else ""
    return (
        f"Predicted {result['diagnosis']} with {result['confidence']:.0%} confidence"
        f"{basis}."
    )


def run_diagnosis(
    symptoms: dict[str, Any], image_url: str | None = None, model_path: Path | None = None
) -> dict[str, Any]:
    try:
        result = predict(symptoms, model_path=model_path)
    except FileNotFoundError as exc:
        raise ApiError(
            code="MODEL_NOT_TRAINED",
            message="The symptom model hasn't been trained yet — run training.symptom_model_train.",
            status_code=503,
        ) from exc

    return {
        "diagnosis": result["diagnosis"],
        "confidence": result["confidence"],
        "explanation": _explanation(result),
        "recommended_action": _recommended_action(result["diagnosis"]),
        "sources": [],
    }
