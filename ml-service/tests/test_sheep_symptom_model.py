from pathlib import Path

import pytest

from app.models.sheep_symptom_model import DISEASES, FEATURES, predict
from training.sheep_symptom_model_train import DATA_PATH, train

ALL_PRESENT = {feature: True for feature in FEATURES}
ALL_ABSENT = {feature: False for feature in FEATURES}


@pytest.fixture(scope="module")
def model_path(tmp_path_factory) -> Path:
    if not DATA_PATH.exists():
        pytest.skip(f"{DATA_PATH} not present locally — see data/sheep-symptoms/SOURCE.md to fetch it")

    trained_model_path = tmp_path_factory.mktemp("models") / "sheep_symptom_model.pkl"
    train(model_path=trained_model_path)
    return trained_model_path


def test_all_symptoms_present_predicts_ppr_positive(model_path):
    result = predict(ALL_PRESENT, model_path=model_path)

    assert result["diagnosis"] == "PPR (Peste des Petits Ruminants)"
    assert result["confidence"] >= 0.4
    assert len(result["top_features"]) > 0


def test_all_symptoms_absent_predicts_ppr_negative(model_path):
    result = predict(ALL_ABSENT, model_path=model_path)

    assert result["diagnosis"] == "PPR Negative"
    assert result["confidence"] >= 0.4


def test_all_missing_returns_uncertain(model_path):
    result = predict({}, model_path=model_path)

    # Zero evidence with only 2 classes gives a uniform-prior confidence of 0.5, which is
    # *above* CONFIDENCE_THRESHOLD (0.4) — that threshold only gates real predictions below,
    # not this early "no evidence at all" return, so this can't reuse the 5-class cow model
    # test's `< 0.4` assertion (1/5 = 0.2 there, 1/2 = 0.5 here).
    assert result["diagnosis"] == "uncertain"
    assert result["confidence"] == pytest.approx(0.5)
    assert result["top_features"] == []


def test_unknown_keys_are_ignored(model_path):
    case = {**ALL_PRESENT, "some_future_symptom": True, "another_one": "x"}
    result = predict(case, model_path=model_path)

    assert result["diagnosis"] == "PPR (Peste des Petits Ruminants)"


def test_diseases_is_binary():
    assert DISEASES == ["PPR Negative", "PPR (Peste des Petits Ruminants)"]
