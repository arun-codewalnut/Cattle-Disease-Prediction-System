from pathlib import Path

import pytest

from app.models.symptom_model import DISEASES, predict
from training.generate_synthetic_data import main as generate_dataset
from training.symptom_model_train import train

ALL_FALSE = {feature: False for feature in [
    "fever", "appetite_loss", "nasal_discharge", "milk_yield_drop", "mouth_lesions",
    "lameness", "excessive_salivation", "skin_nodules", "udder_swelling", "coughing",
    "labored_breathing",
]}

CASE_BY_DISEASE = {
    "Foot and Mouth Disease": {
        "fever": True, "mouth_lesions": True, "excessive_salivation": True,
        "lameness": True, "appetite_loss": True,
    },
    "Lumpy Skin Disease": {
        "fever": True, "skin_nodules": True, "milk_yield_drop": True, "appetite_loss": True,
    },
    "Mastitis": {"milk_yield_drop": True, "udder_swelling": True, "fever": True},
    "Bovine Respiratory Disease": {
        "fever": True, "nasal_discharge": True, "coughing": True, "labored_breathing": True,
    },
    "Healthy": ALL_FALSE,
}


@pytest.fixture(scope="module")
def model_path(tmp_path_factory) -> Path:
    data_path = tmp_path_factory.mktemp("data") / "symptom_dataset.csv"
    generate_dataset(seed=7, out_path=data_path)

    trained_model_path = tmp_path_factory.mktemp("models") / "symptom_model.pkl"
    train(data_path=data_path, model_path=trained_model_path)
    return trained_model_path


def test_confident_prediction_has_shape(model_path):
    result = predict(CASE_BY_DISEASE["Foot and Mouth Disease"], model_path=model_path)

    assert result["diagnosis"] != "uncertain"
    assert result["confidence"] >= 0.4
    assert len(result["top_features"]) > 0
    for entry in result["top_features"]:
        assert set(entry.keys()) == {"feature", "contribution"}


def test_all_missing_returns_uncertain(model_path):
    result = predict({}, model_path=model_path)

    assert result["diagnosis"] == "uncertain"
    assert result["confidence"] < 0.4
    assert result["top_features"] == []


def test_unknown_keys_are_ignored(model_path):
    case = {**CASE_BY_DISEASE["Mastitis"], "some_future_symptom": True, "another_one": "x"}
    result = predict(case, model_path=model_path)

    assert result["diagnosis"] == "Mastitis"


@pytest.mark.parametrize("disease", DISEASES)
def test_one_representative_case_per_class(model_path, disease):
    result = predict(CASE_BY_DISEASE[disease], model_path=model_path)

    assert result["diagnosis"] == disease
