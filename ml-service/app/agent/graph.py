"""
LangGraph agent wiring — stub.

M5 (see docs/ROADMAP.md) replaces this with a real graph: intake -> route -> predict
(tabular/image model tools) -> explain (RAG-grounded) -> recommend_action. Keep it as an
explicit LangGraph StateGraph so the flow stays auditable, not a free-form agent loop —
this is a diagnosis tool, decisions need to be traceable.
"""

from typing import Any


def run_diagnosis(symptoms: dict[str, Any], image_url: str | None = None) -> dict[str, Any]:
    return {
        "diagnosis": "unknown",
        "confidence": 0.0,
        "explanation": "Agent not wired up yet — see agents/playbooks/add-disease-model.md.",
        "recommended_action": "consult_vet",
        "sources": [],
    }
