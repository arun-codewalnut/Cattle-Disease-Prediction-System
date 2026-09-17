"""
Agent wiring for /agent/diagnose — a real LangGraph StateGraph, not a free-form agent loop,
so every path through the system is known in advance and auditable (this is a diagnosis
tool; decisions need to stay traceable). See docs/specs/M5-langgraph-agent-orchestration.md.

What this graph does NOT do: it doesn't change the diagnosis, confidence, or
recommended_action logic — those are exactly what M1/M2 already computed. The only new
observable behavior is that `explain` generates real LLM text (falling back to the old
template if the LLM is unavailable), grounded strictly in the model's own output, not
retrieved documents (that's M6).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.agent.llm import get_llm
from app.errors import ApiError
from app.models.symptom_model import predict

# Diseases that must always escalate regardless of model confidence, per docs/DISCLAIMER.md.
# Deliberately a fixed, auditable list here rather than anything the model (or the LLM)
# could drift on.
REPORTABLE_DISEASES = {"Foot and Mouth Disease", "Lumpy Skin Disease"}

EXPLAIN_SYSTEM_PROMPT = (
    "You are explaining a machine-learning cattle disease prediction to a farmer. Only use "
    "the diagnosis, confidence, and contributing symptoms given to you — do not invent "
    "additional medical facts, causes, or treatment advice beyond what is provided. Keep it "
    "to 2-3 plain-language sentences."
)


class DiagnosisState(TypedDict, total=False):
    symptoms: dict[str, Any]
    image_url: str | None
    model_path: Path | None
    diagnosis: str
    confidence: float
    top_features: list[dict[str, Any]]
    explanation: str
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
    return "predict_image" if state.get("image_url") else "predict_symptoms"


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


def predict_image_node(state: DiagnosisState) -> dict[str, Any]:
    raise ApiError(
        code="NOT_IMPLEMENTED",
        message="Image-based prediction isn't implemented yet.",
        status_code=501,
    )


def explain_node(state: DiagnosisState) -> dict[str, Any]:
    if state["diagnosis"] == "uncertain":
        return {"explanation": _template_explanation(state)}

    try:
        llm = get_llm()
        top_feature_names = [f["feature"] for f in state.get("top_features") or []]
        human_prompt = (
            f"Diagnosis: {state['diagnosis']}\n"
            f"Confidence: {state['confidence']:.0%}\n"
            f"Top contributing symptoms: {', '.join(top_feature_names) or 'none'}\n\n"
            "Explain this result to the farmer."
        )
        response = llm.invoke(
            [SystemMessage(content=EXPLAIN_SYSTEM_PROMPT), HumanMessage(content=human_prompt)]
        )
        return {"explanation": response.content}
    except Exception:
        # Any LLM failure (connection refused, timeout, malformed response, ...) degrades to
        # the deterministic template — a diagnosis tool cannot go down because a local LLM
        # daemon isn't running. See docs/specs/M5-langgraph-agent-orchestration.md.
        return {"explanation": _template_explanation(state)}


def recommend_node(state: DiagnosisState) -> dict[str, Any]:
    return {"recommended_action": _recommended_action(state["diagnosis"]), "sources": []}


def _build_graph():
    builder = StateGraph(DiagnosisState)
    builder.add_node("intake", intake_node)
    builder.add_node("predict_symptoms", predict_symptoms_node)
    builder.add_node("predict_image", predict_image_node)
    builder.add_node("explain", explain_node)
    builder.add_node("recommend", recommend_node)

    builder.set_entry_point("intake")
    builder.add_conditional_edges(
        "intake",
        route_after_intake,
        {"predict_symptoms": "predict_symptoms", "predict_image": "predict_image"},
    )
    builder.add_edge("predict_symptoms", "explain")
    builder.add_edge("explain", "recommend")
    builder.add_edge("recommend", END)
    builder.add_edge("predict_image", END)  # unreachable in practice — the node always raises

    return builder.compile()


_compiled_graph = _build_graph()


def run_diagnosis(
    symptoms: dict[str, Any], image_url: str | None = None, model_path: Path | None = None
) -> dict[str, Any]:
    final_state = _compiled_graph.invoke(
        {"symptoms": symptoms, "image_url": image_url, "model_path": model_path}
    )
    return {
        "diagnosis": final_state["diagnosis"],
        "confidence": final_state["confidence"],
        "explanation": final_state["explanation"],
        "recommended_action": final_state["recommended_action"],
        "sources": final_state.get("sources", []),
    }
