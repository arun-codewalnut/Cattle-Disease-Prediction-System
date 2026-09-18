"""
Agent wiring for /agent/diagnose — a real LangGraph StateGraph, not a free-form agent loop,
so every path through the system is known in advance and auditable (this is a diagnosis
tool; decisions need to stay traceable). See docs/specs/M5-langgraph-agent-orchestration.md
and docs/specs/M6-rag-knowledge-base.md.

What this graph does NOT do: it doesn't change the diagnosis, confidence, or
recommended_action logic — those are exactly what M1/M2 already computed. `explain`
generates real LLM text (falling back to a template if the LLM is unavailable), grounded in
the model's own output plus (M6) retrieved reference passages — never facts invented beyond
what it's given.

`predict_image` (M8 phase 1) is a deterministic placeholder, not a trained model — see
docs/specs/M8-image-diagnosis-phase1.md. It still flows through `recommend`, so the
REPORTABLE_DISEASES escalation rule applies identically regardless of which path produced
the diagnosis.

`precautions` (M10) is a deterministic lookup, not LLM-generated — unlike `explanation`, its
content is reviewed, static text returned verbatim by diagnosis, so it can never soften the
REPORTABLE_DISEASES escalation rule. See docs/specs/M10-precautions-next-steps.md.
"""
from __future__ import annotations

import base64
import binascii
import hashlib
from pathlib import Path
from typing import Any, TypedDict

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.agent.llm import get_llm
from app.errors import ApiError
from app.models.symptom_model import predict
from app.rag.retrieval import get_precautions, retrieve

# Diseases that must always escalate regardless of model confidence, per docs/DISCLAIMER.md.
# Deliberately a fixed, auditable list here rather than anything the model (or the LLM)
# could drift on.
REPORTABLE_DISEASES = {"Foot and Mouth Disease", "Lumpy Skin Disease"}

# M8 phase 1: no trained image model exists yet (see docs/specs/M8-image-diagnosis-phase1.md).
# This is a deterministic hash of the image bytes, not a classifier — it exists only to
# exercise the upload -> diagnosis -> escalation pipeline end to end. One reportable disease
# is deliberately included so the escalation rule gets exercised by the image path too, not
# just the symptom path.
_PLACEHOLDER_DIAGNOSES = ("Healthy", "Lumpy Skin Disease", "Mastitis")
_PLACEHOLDER_CONFIDENCE = 0.5

EXPLAIN_SYSTEM_PROMPT = (
    "You are explaining a machine-learning cattle disease prediction to a farmer. Only use "
    "the diagnosis, confidence, contributing symptoms, and reference material given to you "
    "— do not invent additional medical facts, causes, or treatment advice beyond what is "
    "provided. Keep it to 2-3 plain-language sentences."
)


class DiagnosisState(TypedDict, total=False):
    symptoms: dict[str, Any]
    image_url: str | None
    image_base64: str | None
    model_path: Path | None
    diagnosis: str
    confidence: float
    top_features: list[dict[str, Any]]
    image_placeholder: bool
    explanation: str
    precautions: list[str]
    next_steps: list[str]
    recommended_action: str
    sources: list[str]


def _recommended_action(diagnosis: str) -> str:
    if diagnosis in REPORTABLE_DISEASES:
        return "escalate_to_vet"
    if diagnosis == "uncertain":
        return "consult_vet"
    if diagnosis == "Healthy":
        return "monitor"
    return "consult_vet"


def _template_explanation(state: DiagnosisState) -> str:
    if state["diagnosis"] == "uncertain":
        return (
            "Not enough symptom information was provided to make a confident prediction. "
            "Provide more symptom details or consult a vet directly."
        )
    top_feature_names = [f["feature"] for f in state.get("top_features") or []]
    basis = f", based primarily on: {', '.join(top_feature_names)}" if top_feature_names else ""
    return f"Predicted {state['diagnosis']} with {state['confidence']:.0%} confidence{basis}."


def intake_node(state: DiagnosisState) -> dict[str, Any]:
    # Nothing to normalize — the request shape is already validated by app/api/diagnose.py's
    # Pydantic model. This node exists so intake is an explicit, visible step in the graph.
    return {}


def route_after_intake(state: DiagnosisState) -> str:
    has_image = bool(state.get("image_url") or state.get("image_base64"))
    return "predict_image" if has_image else "predict_symptoms"


def predict_symptoms_node(state: DiagnosisState) -> dict[str, Any]:
    try:
        result = predict(state["symptoms"], model_path=state.get("model_path"))
    except FileNotFoundError as exc:
        raise ApiError(
            code="MODEL_NOT_TRAINED",
            message="The symptom model hasn't been trained yet — run training.symptom_model_train.",
            status_code=503,
        ) from exc

    return {
        "diagnosis": result["diagnosis"],
        "confidence": result["confidence"],
        "top_features": result["top_features"],
    }


def _fetch_image_bytes(state: DiagnosisState) -> bytes | None:
    image_base64 = state.get("image_base64")
    if image_base64:
        try:
            return base64.b64decode(image_base64, validate=True)
        except (binascii.Error, ValueError):
            return None

    image_url = state.get("image_url")
    if image_url:
        try:
            response = httpx.get(image_url, timeout=3.0)
            response.raise_for_status()
            return response.content
        except httpx.HTTPError:
            return None

    return None


def predict_image_node(state: DiagnosisState) -> dict[str, Any]:
    image_bytes = _fetch_image_bytes(state)

    if image_bytes is None:
        # Undecodable base64 or an unreachable image_url — degrade to "uncertain" rather
        # than failing the request, same "never blocks a diagnosis" pattern as explain_node.
        return {
            "diagnosis": "uncertain",
            "confidence": 0.0,
            "top_features": [],
            "image_placeholder": True,
        }

    digest = hashlib.sha256(image_bytes).digest()
    diagnosis = _PLACEHOLDER_DIAGNOSES[digest[0] % len(_PLACEHOLDER_DIAGNOSES)]

    return {
        "diagnosis": diagnosis,
        "confidence": _PLACEHOLDER_CONFIDENCE,
        "top_features": [],
        "image_placeholder": True,
    }


def explain_node(state: DiagnosisState) -> dict[str, Any]:
    if state.get("image_placeholder"):
        # Deliberately skips the LLM/RAG path entirely (unlike the symptom flow) so a
        # placeholder result can never be phrased indistinguishably from a real, grounded
        # explanation — see docs/specs/M8-image-diagnosis-phase1.md.
        return {
            "explanation": (
                f"This is a placeholder image-based prediction ({state['diagnosis']}, "
                f"{state['confidence']:.0%} confidence). No trained image-recognition model "
                "exists yet — this result only demonstrates the upload-to-response pipeline "
                "and must not be used for any real decision."
            ),
            "sources": [],
        }

    if state["diagnosis"] == "uncertain":
        return {"explanation": _template_explanation(state), "sources": []}

    # Retrieval failure (Chroma unreachable, empty collection) degrades to no retrieved
    # context, same as an LLM failure degrades to the template — never blocks a diagnosis.
    # retrieve() itself never raises (see app/rag/retrieval.py), but stay defensive here too.
    try:
        retrieved = retrieve(state["diagnosis"])
    except Exception:
        retrieved = []

    try:
        llm = get_llm()
        top_feature_names = [f["feature"] for f in state.get("top_features") or []]
        context_block = ""
        if retrieved:
            passages = "\n\n".join(f"[{r['source']}] {r['text']}" for r in retrieved)
            context_block = f"\n\nReference material:\n{passages}"
        human_prompt = (
            f"Diagnosis: {state['diagnosis']}\n"
            f"Confidence: {state['confidence']:.0%}\n"
            f"Top contributing symptoms: {', '.join(top_feature_names) or 'none'}"
            f"{context_block}\n\n"
            "Explain this result to the farmer, drawing on the reference material above "
            "when relevant."
        )
        response = llm.invoke(
            [SystemMessage(content=EXPLAIN_SYSTEM_PROMPT), HumanMessage(content=human_prompt)]
        )
        # Only cite sources that were actually available to the explanation that's being
        # shown — if the LLM call below fails instead, the except branch reports no sources,
        # since the fallback template doesn't reference them.
        sources = sorted({r["source"] for r in retrieved})
        return {"explanation": response.content, "sources": sources}
    except Exception:
        # Any LLM failure (connection refused, timeout, malformed response, ...) degrades to
        # the deterministic template — a diagnosis tool cannot go down because a local LLM
        # daemon isn't running. See docs/specs/M5-langgraph-agent-orchestration.md.
        return {"explanation": _template_explanation(state), "sources": []}


def precautions_node(state: DiagnosisState) -> dict[str, Any]:
    # get_precautions() itself never raises (see app/rag/retrieval.py) — stay defensive
    # here too anyway, same belt-and-suspenders principle explain_node uses around
    # retrieve(): a diagnosis must never fail because guidance text couldn't be looked up.
    try:
        result = get_precautions(state["diagnosis"])
    except Exception:
        return {"precautions": [], "next_steps": []}
    return {"precautions": result["precautions"], "next_steps": result["next_steps"]}


def recommend_node(state: DiagnosisState) -> dict[str, Any]:
    return {"recommended_action": _recommended_action(state["diagnosis"])}


def _build_graph():
    builder = StateGraph(DiagnosisState)
    builder.add_node("intake", intake_node)
    builder.add_node("predict_symptoms", predict_symptoms_node)
    builder.add_node("predict_image", predict_image_node)
    builder.add_node("explain", explain_node)
    builder.add_node("add_precautions", precautions_node)
    builder.add_node("recommend", recommend_node)

    builder.set_entry_point("intake")
    builder.add_conditional_edges(
        "intake",
        route_after_intake,
        {"predict_symptoms": "predict_symptoms", "predict_image": "predict_image"},
    )
    builder.add_edge("predict_symptoms", "explain")
    builder.add_edge("predict_image", "explain")
    builder.add_edge("explain", "add_precautions")
    builder.add_edge("add_precautions", "recommend")
    builder.add_edge("recommend", END)

    return builder.compile()


_compiled_graph = _build_graph()


def run_diagnosis(
    symptoms: dict[str, Any],
    image_url: str | None = None,
    image_base64: str | None = None,
    model_path: Path | None = None,
) -> dict[str, Any]:
    final_state = _compiled_graph.invoke(
        {
            "symptoms": symptoms,
            "image_url": image_url,
            "image_base64": image_base64,
            "model_path": model_path,
        }
    )
    return {
        "diagnosis": final_state["diagnosis"],
        "confidence": final_state["confidence"],
        "explanation": final_state["explanation"],
        "recommended_action": final_state["recommended_action"],
        "sources": final_state.get("sources", []),
        "precautions": final_state.get("precautions", []),
        "next_steps": final_state.get("next_steps", []),
    }
