import pytest

# chromadb has no cp313 wheel on Windows (see ml-service/AGENTS.md) — skip this whole file
# cleanly (not an error) when it's not installed natively; run these via Docker instead.
pytest.importorskip("chromadb")

from app.agent.graph import REPORTABLE_DISEASES  # noqa: E402
from app.rag.retrieval import get_precautions, retrieve  # noqa: E402


def test_retrieve_returns_relevant_chunk_for_known_disease():
    results = retrieve("Foot and Mouth Disease", k=3)

    assert len(results) > 0
    assert any(r["source"] == "foot-and-mouth-disease" for r in results)
    assert all({"text", "source"} <= r.keys() for r in results)


def test_retrieve_different_diseases_return_different_top_source():
    fmd_results = retrieve("Foot and Mouth Disease blisters mouth lesions", k=1)
    mastitis_results = retrieve("Mastitis udder swelling milk yield", k=1)

    assert fmd_results[0]["source"] == "foot-and-mouth-disease"
    assert mastitis_results[0]["source"] == "mastitis"


def test_retrieve_from_empty_collection_returns_empty_list(tmp_path):
    results = retrieve("anything", persist_dir=tmp_path / "empty-collection")

    assert results == []


def test_retrieve_never_raises_on_backend_error(monkeypatch):
    import app.rag.retrieval as retrieval_module

    def _broken_get_collection(persist_dir=None):
        raise RuntimeError("simulated Chroma failure")

    monkeypatch.setattr(retrieval_module, "_get_collection", _broken_get_collection)

    results = retrieve("anything")

    assert results == []


def test_retrieve_never_surfaces_precautions_or_next_steps_chunks():
    # M10 added precautions/next-steps content to the same collection retrieve() searches —
    # must stay invisible to it, since that content is never meant to feed the LLM-grounded
    # explanation prompt (see docs/specs/M10-precautions-next-steps.md).
    for query in ("Foot and Mouth Disease", "Lumpy Skin Disease", "Mastitis"):
        results = retrieve(query, k=5)
        for r in results:
            assert "Contact your veterinarian" not in r["text"]
            assert "Isolate the affected animal" not in r["text"]


def test_get_precautions_returns_content_for_known_disease():
    result = get_precautions("Mastitis")

    assert len(result["precautions"]) > 0
    assert len(result["next_steps"]) > 0
    assert all(isinstance(item, str) and item for item in result["precautions"])


def test_get_precautions_reportable_diseases_always_advise_escalation():
    # The one thing this feature must never get wrong, per docs/DISCLAIMER.md: precautions
    # for a reportable disease must never read as "no action needed."
    for disease in REPORTABLE_DISEASES:
        result = get_precautions(disease)
        next_steps_text = " ".join(result["next_steps"]).lower()
        assert "vet" in next_steps_text or "authority" in next_steps_text or "authorities" in next_steps_text


def test_get_precautions_healthy_returns_preventive_guidance():
    result = get_precautions("Healthy")

    assert len(result["precautions"]) > 0
    assert len(result["next_steps"]) > 0


def test_get_precautions_uncertain_returns_hardcoded_guidance():
    result = get_precautions("uncertain")

    assert result["precautions"] == ["Keep monitoring the animal closely for any new or worsening symptoms."]
    assert result["next_steps"] == [
        "Provide more symptom details for a more confident prediction, or consult a vet directly."
    ]


def test_get_precautions_unknown_diagnosis_returns_empty_lists():
    result = get_precautions("Not A Real Disease")

    assert result == {"precautions": [], "next_steps": []}


def test_get_precautions_never_raises_on_backend_error(monkeypatch):
    import app.rag.retrieval as retrieval_module

    def _broken_get_collection(persist_dir=None):
        raise RuntimeError("simulated Chroma failure")

    monkeypatch.setattr(retrieval_module, "_get_collection", _broken_get_collection)

    result = get_precautions("Mastitis")

    assert result == {"precautions": [], "next_steps": []}
