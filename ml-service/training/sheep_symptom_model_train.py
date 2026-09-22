"""
Trains the M12 follow-up Sheep symptom model — a real, trained binary PPR (Peste des
Petits Ruminants) screen, replacing the cow-model approximation Sheep used to get.

See docs/specs/M12-sheep-disease-detection.md and data/sheep-symptoms/SOURCE.md for why this
is trained on the full goat+sheep dataset (not a "sheep-only" subset — the `animal` column's
0/1 encoding is undocumented and unverifiable, so isolating sheep rows isn't possible without
guessing). Run from ml-service/ (venv active):

    python -m training.sheep_symptom_model_train

No `generate_synthetic_data` step needed first — unlike the cattle symptom model, this
dataset arrives pre-collected (real field data, CTGAN-augmented by its own author) in
data/sheep-symptoms/PPR-Goats-Sheep.csv. See that folder's SOURCE.md to redownload it.
"""
from __future__ import annotations

import pickle
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold

from app.models.sheep_symptom_model import DISEASES, FEATURES

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "sheep-symptoms" / "PPR-Goats-Sheep.csv"
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "sheep_symptom_model.pkl"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "models" / "REGISTRY.md"

XGB_PARAMS = {
    "objective": "multi:softprob",
    "num_class": len(DISEASES),
    "max_depth": 4,
    "eta": 0.2,
    "eval_metric": "mlogloss",
    "seed": 42,
}
NUM_BOOST_ROUND = 60


def load_dataset(path: Path) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_csv(path)
    x = df[FEATURES].astype(float).to_numpy()
    # result: 0 = PPR negative, 1 = PPR positive — matches DISEASES' index order exactly,
    # so no label_to_idx remapping is needed (unlike symptom_model_train.py, whose CSV has
    # a string `diagnosis` column instead of an already-integer-coded target).
    y = df["result"].astype(int).to_numpy()
    return x, y


def train(data_path: Path = DATA_PATH, model_path: Path = MODEL_PATH) -> dict:
    x, y = load_dataset(data_path)

    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    fold_accuracies: list[float] = []
    fold_f1_macro: list[float] = []
    per_class_f1_totals = np.zeros(len(DISEASES))

    for train_idx, test_idx in skf.split(x, y):
        dtrain = xgb.DMatrix(x[train_idx], label=y[train_idx], feature_names=FEATURES, missing=np.nan)
        dtest = xgb.DMatrix(x[test_idx], feature_names=FEATURES, missing=np.nan)
        booster = xgb.train(XGB_PARAMS, dtrain, num_boost_round=NUM_BOOST_ROUND)
        preds = np.argmax(booster.predict(dtest), axis=1)

        fold_accuracies.append(accuracy_score(y[test_idx], preds))
        fold_f1_macro.append(f1_score(y[test_idx], preds, average="macro"))
        per_class_f1_totals += f1_score(
            y[test_idx], preds, average=None, labels=range(len(DISEASES)), zero_division=0
        )

    per_class_f1 = (per_class_f1_totals / skf.get_n_splits()).tolist()

    dfull = xgb.DMatrix(x, label=y, feature_names=FEATURES, missing=np.nan)
    final_booster = xgb.train(XGB_PARAMS, dfull, num_boost_round=NUM_BOOST_ROUND)

    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as f:
        pickle.dump({"booster": final_booster, "label_names": DISEASES}, f)

    return {
        "n_samples": len(y),
        "class_distribution": {name: int((y == i).sum()) for i, name in enumerate(DISEASES)},
        "cv_accuracy_mean": float(np.mean(fold_accuracies)),
        "cv_f1_macro_mean": float(np.mean(fold_f1_macro)),
        "cv_f1_per_class": dict(zip(DISEASES, per_class_f1)),
    }


def update_registry(metrics: dict, model_path: Path = MODEL_PATH, registry_path: Path = REGISTRY_PATH) -> None:
    entry = (
        f"| `{model_path.name}` | PPR (Peste des Petits Ruminants) — binary, goat+sheep "
        f"combined (see SOURCE.md — species column undecodable) | "
        f"sheep-symptoms/PPR-Goats-Sheep.csv ({metrics['n_samples']} rows) | "
        f"acc={metrics['cv_accuracy_mean']:.3f}, f1_macro={metrics['cv_f1_macro_mean']:.3f} | "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')} |\n"
    )
    text = registry_path.read_text(encoding="utf-8")
    registry_path.write_text(text + entry, encoding="utf-8")


if __name__ == "__main__":
    result_metrics = train()
    print(result_metrics)
    update_registry(result_metrics)
