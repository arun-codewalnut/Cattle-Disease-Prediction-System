import base64
from pathlib import Path
from types import SimpleNamespace

import app.agent.graph as graph_module
import app.models.image_model as image_model_module
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


# M9: the real image_model.pt artifact and cattle-images dataset are both gitignored (large,
# unverified-license real photos), so CI won't have them — tests needing a real confident
# image prediction skip gracefully there. See docs/specs/M9-cattle-image-classifier.md.
_IMAGE_MODEL_PATH = image_model_module.DEFAULT_MODEL_PATH
_CATTLE_IMAGES_DIR = Path(__file__).resolve().parents[1] / "data" / "cattle-images"
_HAS_TRAINED_IMAGE_MODEL = _IMAGE_MODEL_PATH.exists()


def _sample_image_base64(folder: str) -> str:
    sample = next((_CATTLE_IMAGES_DIR / folder).glob("*.jpg"))
    return base64.b64encode(sample.read_bytes()).decode()


@pytest.mark.skipif(not _HAS_TRAINED_IMAGE_MODEL, reason="no local ml-service/models/image_model.pt")
def test_image_base64_produces_a_real_diagnosis_per_class():
    for folder, expected in [
        ("healthy", "Healthy"),
        ("lumpy", "Lumpy Skin Disease"),
        ("foot-and-mouth", "Foot and Mouth Disease"),
    ]:
        result = run_diagnosis({}, image_base64=_sample_image_base64(folder))
        assert result["diagnosis"] == expected
        assert result["sources"] == [] or isinstance(result["sources"], list)


@pytest.mark.skipif(not _HAS_TRAINED_IMAGE_MODEL, reason="no local ml-service/models/image_model.pt")
def test_image_diagnosis_uses_the_real_llm_rag_explain_path(monkeypatch):
    # Unlike the M8 placeholder, a real image diagnosis now goes through the same explain
    # path as symptoms — get_llm() gets called, not skipped.
    calls = []

    class FakeLLM:
        def invoke(self, messages):
            calls.append("called")
            return SimpleNamespace(content="Grounded explanation.")

    monkeypatch.setattr(graph_module, "get_llm", lambda: FakeLLM())

    result = run_diagnosis({}, image_base64=_sample_image_base64("lumpy"))

    assert calls == ["called"]
    assert result["explanation"] == "Grounded explanation."


@pytest.mark.skipif(not _HAS_TRAINED_IMAGE_MODEL, reason="no local ml-service/models/image_model.pt")
def test_image_diagnosis_still_escalates_for_reportable_disease():
    result = run_diagnosis({}, image_base64=_sample_image_base64("lumpy"))

    assert result["diagnosis"] == "Lumpy Skin Disease"
    assert result["recommended_action"] == "escalate_to_vet"


def test_image_bytes_that_arent_a_real_image_degrade_to_uncertain():
    # Valid base64, but not a decodable image — app/models/image_model.py's own PIL-decode
    # failure path, distinct from _fetch_image_bytes's "couldn't even get bytes" cases below.
    image_base64 = base64.b64encode(b"not a real image, just arbitrary bytes").decode()

    result = run_diagnosis({}, image_base64=image_base64)

    assert result["diagnosis"] == "uncertain"
    assert result["recommended_action"] == "consult_vet"


# A tiny real 1x1 PNG, already base64-encoded — genuinely decodable, so tests using it
# exercise the "model missing" path specifically, not the "not a real image" decode-failure
# path tested above.
_VALID_1X1_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def test_missing_image_model_returns_structured_error(monkeypatch, tmp_path):
    # Always runs, everywhere — the actual behavior CI sees, since image_model.pt is
    # gitignored and not committed.
    monkeypatch.setattr(image_model_module, "DEFAULT_MODEL_PATH", tmp_path / "does-not-exist.pt")

    with pytest.raises(ApiError) as exc_info:
        run_diagnosis({}, image_base64=_VALID_1X1_PNG_BASE64)

    assert exc_info.value.code == "MODEL_NOT_TRAINED"


def test_invalid_image_base64_degrades_to_uncertain_instead_of_failing():
    result = run_diagnosis({}, image_base64="not valid base64!!!")

    assert result["diagnosis"] == "uncertain"
    assert result["recommended_action"] == "consult_vet"


def test_unreachable_image_url_degrades_to_uncertain_instead_of_failing():
    result = run_diagnosis({}, image_url="http://127.0.0.1:1/does-not-resolve.jpg")

    assert result["diagnosis"] == "uncertain"
    assert result["recommended_action"] == "consult_vet"


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


def test_uncertain_diagnosis_gets_hardcoded_precautions():
    # "uncertain" isn't a disease, so get_precautions() short-circuits before touching
    # Chroma at all (see app/rag/retrieval.py) — this runs natively, no chromadb needed,
    # unlike the real-disease precautions tests in test_rag_retrieval.py.
    result = run_diagnosis({})

    assert result["diagnosis"] == "uncertain"
    assert result["precautions"] == ["Keep monitoring the animal closely for any new or worsening symptoms."]
    assert result["next_steps"] == [
        "Provide more symptom details for a more confident prediction, or consult a vet directly."
    ]


def test_precautions_lookup_failure_does_not_block_diagnosis(monkeypatch):
    def _broken_get_precautions(diagnosis, persist_dir=None):
        raise RuntimeError("simulated Chroma failure")

    monkeypatch.setattr(graph_module, "get_precautions", _broken_get_precautions)

    result = run_diagnosis(CONFIDENT_SYMPTOMS)

    assert result["diagnosis"] == "Foot and Mouth Disease"
    assert result["precautions"] == []
    assert result["next_steps"] == []
