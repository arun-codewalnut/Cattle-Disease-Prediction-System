"""
Session-wide fixture: trains a real symptom model once per test run and points the app's
default path at it, so any test hitting the API works without a committed model artifact.
test_symptom_model.py's own fixture trains a separate model and passes it explicitly —
that's deliberate, not redundant: it's testing predict()'s model_path parameter directly.

There is no RAG fixture any more. Retrieval reads the checked-in markdown documents
directly (docs/specs/remove-databases.md), so there is nothing to ingest and nothing to
point at a temporary directory.
"""
import app.agent.graph as graph_module
import app.models.symptom_model as symptom_model_module
import pytest
from training.generate_synthetic_data import main as generate_dataset
from training.symptom_model_train import train


@pytest.fixture(scope="session", autouse=True)
def _trained_default_model(tmp_path_factory):
    data_path = tmp_path_factory.mktemp("data") / "symptom_dataset.csv"
    generate_dataset(seed=42, out_path=data_path)

    model_path = tmp_path_factory.mktemp("models") / "symptom_model.pkl"
    train(data_path=data_path, model_path=model_path)

    symptom_model_module.DEFAULT_MODEL_PATH = model_path
    return model_path



@pytest.fixture(autouse=True)
def _no_real_llm_calls(monkeypatch):
    """Fails fast instead of actually trying to reach Ollama (which isn't running in this
    environment) and waiting out the connection timeout on every confident-diagnosis test.
    This is also the honest default: no LLM is available here, so `explain` should exercise
    its fallback path by default. Tests that want the LLM-success path override this
    locally with their own `monkeypatch.setattr(graph_module, "get_llm", ...)`."""

    def _raise():
        raise RuntimeError("no LLM available in tests by default — see conftest.py")

    monkeypatch.setattr(graph_module, "get_llm", _raise)
