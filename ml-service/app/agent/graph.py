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

`predict_image` (M9) is a real, trained MobileNetV2-transfer-learning classifier — see
docs/specs/M9-cattle-image-classifier.md. It covers only 3 of the symptom model's 5 diseases
(Healthy / Lumpy Skin Disease / Foot and Mouth Disease — no Mastitis/Bovine Respiratory
Disease image data exists). It flows through `recommend` exactly like the symptom path, so
the REPORTABLE_DISEASES escalation rule applies identically regardless of which path produced
the diagnosis.

`predict_image` is species-aware (M13/M14 follow-up, real Cat/Dog models): `species` in the
request picks which trained model runs — Cat and Dog get their own models
(`app/models/cat_image_model.py`/`dog_image_model.py`), everything else (Cow/Sheep, or no
species given) falls back to the cattle model above, unchanged. The Cat model is solid
(83% accuracy). **The Dog model is genuinely weak (52.6% accuracy, 0.25 F1 for Canine
Distemper specifically)** — shipped anyway per an explicit decision to disclose loudly rather
than withhold, not silently trusted. Nothing here softens that; the caveat lives in the
frontend and `docs/DISCLAIMER.md`, not swept into a confidence number alone.

`predict_symptoms` is now species-aware too (M12 follow-up): Sheep routes to its own real,
trained binary PPR (Peste des Petits Ruminants) screen (`app/models/sheep_symptom_model.py`)
instead of silently sharing the cattle model like it (and the now-removed Buffalo species)
used to. Everything else still uses the cattle symptom model unchanged.

`predict_image` (M15 follow-up) now runs every photo through `app/models/species_gate.py`
first — a free, pretrained "is this even an animal" check — before calling any
species-specific disease model. A photo that isn't of an animal at all (a car, furniture,
...) never reaches the disease classifier; it comes back as `diagnosis: "invalid_image"`
instead, a distinct sentinel from `"uncertain"` (which still means "a real animal photo, just
not a confident disease match"). See docs/specs/M15-image-diagnosis-quality-gate.md.

`precautions` (M10) is a deterministic lookup, not LLM-generated — unlike `explanation`, its
content is reviewed, static text returned verbatim by diagnosis, so it can never soften the
REPORTABLE_DISEASES escalation rule. See docs/specs/M10-precautions-next-steps.md.
"""
from __future__ import annotations

import base64
import binascii
from pathlib import Path
from typing import Any, TypedDict

import httpx
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.agent.llm import get_llm
from app.errors import ApiError
from app.models import cat_image_model, dog_image_model, species_gate
from app.models import image_model as cattle_image_model
from app.models import sheep_symptom_model
from app.models import symptom_model as cattle_symptom_model
from app.rag.retrieval import get_precautions, retrieve

# Diseases that must always escalate regardless of model confidence, per docs/DISCLAIMER.md.
# Deliberately a fixed, auditable list here rather than anything the model (or the LLM)
# could drift on. PPR (Peste des Petits Ruminants) is WOAH/OIE-notifiable — same tier of
# seriousness as FMD/LSD, so it escalates the same way.
REPORTABLE_DISEASES = {
    "Foot and Mouth Disease",
    "Lumpy Skin Disease",
    "PPR (Peste des Petits Ruminants)",
}

# Which trained image model handles which species — anything not listed (Cow/Sheep, or no
# species given) falls back to the cattle model, same as before species-aware routing
# existed. See the module docstring above for each model's real accuracy.
_IMAGE_MODEL_BY_SPECIES = {"CAT": cat_image_model, "DOG": dog_image_model}

# Which trained symptom model handles which species — anything not listed falls back to the
# cattle model, same fallback pattern as the image side above.
_SYMPTOM_MODEL_BY_SPECIES = {"SHEEP": sheep_symptom_model}

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
    species: str | None
    model_path: Path | None
    diagnosis: str
    confidence: float
    top_features: list[dict[str, Any]]
    explanation: str
    precautions: list[str]
    next_steps: list[str]
    recommended_action: str
    sources: list[str]


def _recommended_action(diagnosis: str) -> str:
    if diagnosis in REPORTABLE_DISEASES:
        return "escalate_to_vet"
    if diagnosis == "invalid_image":
        # Deliberately not consult_vet/monitor/escalate — nothing was actually diagnosed,
        # so none of the vet-triage actions apply. A distinct value the frontend renders as
        # its own "try again" affordance instead of a diagnosis-result badge.
        return "retry_upload"
    if diagnosis == "uncertain":
        return "consult_vet"
    if diagnosis in ("Healthy", "PPR Negative"):
        return "monitor"
    return "consult_vet"


def _template_explanation(state: DiagnosisState) -> str:
    if state["diagnosis"] == "invalid_image":
        return "This doesn't look like a photo of an animal — please upload a clear photo of the animal itself."
    if state["diagnosis"] == "uncertain":
        was_image = bool(state.get("image_url") or state.get("image_base64"))
        if was_image:
            return (
                "The photo didn't show a clear, confident sign of any recognized condition. "
                "Try a clearer photo focused on the affected area, or consult a vet directly."
            )
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
    model_module = _SYMPTOM_MODEL_BY_SPECIES.get(state.get("species") or "", cattle_symptom_model)

    try:
        result = model_module.predict(state["symptoms"], model_path=state.get("model_path"))
    except FileNotFoundError as exc:
        raise ApiError(
            code="MODEL_NOT_TRAINED",
            message=f"The {model_module.__name__.rsplit('.', 1)[-1]} hasn't been trained yet.",
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
        return {"diagnosis": "uncertain", "confidence": 0.0, "top_features": []}

    if not species_gate.is_animal_photo(image_bytes):
        # Not a decode failure (that's the branch above) — a photo that decoded fine but
        # isn't of an animal at all. Never reaches a disease-specific model; see
        # docs/specs/M15-image-diagnosis-quality-gate.md.
        return {"diagnosis": "invalid_image", "confidence": 0.0, "top_features": []}

    model_module = _IMAGE_MODEL_BY_SPECIES.get(state.get("species") or "", cattle_image_model)

    try:
        result = model_module.predict(image_bytes, model_path=state.get("model_path"))
    except FileNotFoundError as exc:
        raise ApiError(
            code="MODEL_NOT_TRAINED",
            message=f"The {model_module.__name__.rsplit('.', 1)[-1]} hasn't been trained yet.",
            status_code=503,
        ) from exc

    return {
        "diagnosis": result["diagnosis"],
        "confidence": result["confidence"],
        "top_features": result["top_features"],
    }


def explain_node(state: DiagnosisState) -> dict[str, Any]:
    if state["diagnosis"] in ("uncertain", "invalid_image"):
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
    species: str | None = None,
    model_path: Path | None = None,
) -> dict[str, Any]:
    final_state = _compiled_graph.invoke(
        {
            "symptoms": symptoms,
            "image_url": image_url,
            "image_base64": image_base64,
            "species": species,
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
