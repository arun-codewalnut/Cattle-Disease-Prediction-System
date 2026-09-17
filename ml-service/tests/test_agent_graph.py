from types import SimpleNamespace

import app.agent.graph as graph_module
import pytest
from app.agent.graph import run_diagnosis
from app.errors import ApiError

CONFIDENT_SYMPTOMS = {
    "fever": True,
    "mouth_lesions": True,
    "excessive_salivation": True,
    "lameness": True,
    "appetite_loss": True,
}


def test_explain_falls_back_to_template_when_llm_unavailable():
    # conftest.py's autouse fixture makes get_llm() raise by default — this is the honest
    # "no Ollama running" state of this environment, exercised without any extra mocking.
    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["diagnosis"] != "uncertain"
    assert "Predicted" in result["explanation"]
    assert "based primarily on" in result["explanation"]


def test_explain_uses_llm_output_when_available(monkeypatch):
    fake_response = SimpleNamespace(content="The cow likely has FMD based on the classic symptom triad.")

    class FakeLLM:
        def invoke(self, messages):
            return fake_response

    monkeypatch.setattr(graph_module, "get_llm", lambda: FakeLLM())

    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["explanation"] == fake_response.content


def test_explain_llm_failure_mid_call_still_falls_back(monkeypatch):
    class BrokenLLM:
        def invoke(self, messages):
            raise TimeoutError("simulated LLM timeout")

    monkeypatch.setattr(graph_module, "get_llm", lambda: BrokenLLM())

    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert "Predicted" in result["explanation"]
    assert result["diagnosis"] != "uncertain"


def test_uncertain_diagnosis_never_calls_the_llm(monkeypatch):
    calls = []
    monkeypatch.setattr(graph_module, "get_llm", lambda: calls.append("called"))

    result = run_diagnosis({})

    assert result["diagnosis"] == "uncertain"
    assert calls == []


def test_image_url_routes_to_not_implemented():
    with pytest.raises(ApiError) as exc_info:
        run_diagnosis({"fever": True}, image_url="https://example.com/cow.jpg")

    assert exc_info.value.code == "NOT_IMPLEMENTED"
    assert exc_info.value.status_code == 501


def test_recommended_action_still_escalates_for_reportable_disease():
    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["diagnosis"] == "Foot and Mouth Disease"
    assert result["recommended_action"] == "escalate_to_vet"


def test_sources_populated_when_llm_and_retrieval_both_succeed(monkeypatch):
    # chromadb has no cp313 wheel on Windows (see ml-service/AGENTS.md) — this test needs
    # real retrieval to be meaningful, so skip cleanly (not an error) without it; run via
    # Docker instead. The other tests here don't need real chromadb (retrieve() itself
    # degrades to [] gracefully when it's unavailable), so only this one skips.
    pytest.importorskip("chromadb")

    fake_response = SimpleNamespace(content="Grounded explanation using the reference material.")
    monkeypatch.setattr(graph_module, "get_llm", lambda: SimpleNamespace(invoke=lambda messages: fake_response))

    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["explanation"] == fake_response.content
    # Semantic retrieval over small, thematically-similar documents can legitimately surface
    # more than one source (e.g. another viral-disease doc sharing similar language) — the
    # meaningful assertion is that the correct primary document was retrieved, not that it's
    # the only one.
    assert "foot-and-mouth-disease" in result["sources"]
    assert len(result["sources"]) >= 1


def test_sources_empty_when_llm_falls_back_to_template():
    # Default autouse fixture makes get_llm() raise — explanation falls back to the
    # template, which doesn't cite anything, so sources must not claim retrieval was used.
    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["sources"] == []


def test_retrieval_failure_does_not_block_diagnosis(monkeypatch):
    def _broken_retrieve(query, k=3):
        raise RuntimeError("simulated Chroma failure")

    monkeypatch.setattr(graph_module, "retrieve", _broken_retrieve)

    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["diagnosis"] == "Foot and Mouth Disease"
    assert result["sources"] == []


def test_uncertain_diagnosis_never_calls_retrieval(monkeypatch):
    calls = []
    monkeypatch.setattr(graph_module, "retrieve", lambda query, k=3: calls.append(query))

    result = run_diagnosis({})

    assert result["diagnosis"] == "uncertain"
    assert calls == []
