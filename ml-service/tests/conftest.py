"""
Session-wide fixture: trains a real symptom model once per test run and points
`app.models.symptom_model.DEFAULT_MODEL_PATH` at it, so any test hitting the API (which
calls predict() with no explicit model_path) works without needing a committed model
artifact. test_symptom_model.py's own fixture trains a separate model and passes it
explicitly — that's deliberate, not redundant: it's testing predict()'s model_path
parameter directly.
"""
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
