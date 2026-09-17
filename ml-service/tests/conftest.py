"""
Session-wide fixtures: trains a real symptom model and ingests the real RAG reference docs
once per test run, pointing the app's default paths at them, so any test hitting the API
works without needing committed model/Chroma artifacts. test_symptom_model.py's own
fixture trains a separate model and passes it explicitly — that's deliberate, not
redundant: it's testing predict()'s model_path parameter directly.
"""
import app.agent.graph as graph_module
import app.models.symptom_model as symptom_model_module
import app.rag.retrieval as retrieval_module
import pytest
from app.rag.ingest import ingest as ingest_rag_docs
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


@pytest.fixture(scope="session", autouse=True)
def _ingested_rag_knowledge_base(tmp_path_factory):
    """Best-effort — `chromadb` has no cp313 wheel on Windows (see ml-service/AGENTS.md), so
    this must not fail the whole session when it's unavailable natively. Non-RAG tests don't
    need this to succeed at all (retrieve() itself degrades to [] gracefully when chromadb
    can't be imported); RAG-specific tests skip themselves individually via
    `pytest.importorskip("chromadb")` when it's genuinely missing."""
    try:
        persist_dir = tmp_path_factory.mktemp("chroma_db")
        ingest_rag_docs(persist_dir=persist_dir)
        retrieval_module.DEFAULT_PERSIST_DIR = persist_dir
        return persist_dir
    except ImportError:
        return None


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
