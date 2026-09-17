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
