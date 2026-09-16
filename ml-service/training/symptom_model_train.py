"""
Trains the M1 baseline symptom-based disease classifier.

See docs/specs/M1-baseline-symptom-model.md. Run from ml-service/ (venv active):

    python -m training.generate_synthetic_data   # once, or to regenerate
    python -m training.symptom_model_train
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

from app.models.symptom_model import DISEASES, FEATURES

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "symptom_dataset.csv"
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "symptom_model.pkl"
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
    df = pd.read_csv(path, na_values=[""], keep_default_na=True)

    before = len(df)
    df = df.dropna(subset=["diagnosis"])
    dropped = before - len(df)
    if dropped:
        print(f"WARNING: dropped {dropped} row(s) with missing diagnosis label")

    x = df[FEATURES].astype(float).to_numpy()
    y = df["diagnosis"].to_numpy()
    return x, y


def train(data_path: Path = DATA_PATH, model_path: Path = MODEL_PATH) -> dict:
    x, y_raw = load_dataset(data_path)
    label_to_idx = {name: i for i, name in enumerate(DISEASES)}
    y = np.array([label_to_idx[label] for label in y_raw])

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
        "class_distribution": {name: int((y_raw == name).sum()) for name in DISEASES},
        "cv_accuracy_mean": float(np.mean(fold_accuracies)),
        "cv_f1_macro_mean": float(np.mean(fold_f1_macro)),
        "cv_f1_per_class": dict(zip(DISEASES, per_class_f1)),
    }


def update_registry(metrics: dict, model_path: Path = MODEL_PATH, registry_path: Path = REGISTRY_PATH) -> None:
    entry = (
        f"| `{model_path.name}` | all (multiclass) | synthetic-symptom-dataset "
        f"({metrics['n_samples']} rows) | acc={metrics['cv_accuracy_mean']:.3f}, "
        f"f1_macro={metrics['cv_f1_macro_mean']:.3f} | "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')} |\n"
    )
    text = registry_path.read_text(encoding="utf-8")
    placeholder = "| _(none yet)_ | | | | |\n"
    text = text.replace(placeholder, entry) if placeholder in text else text + entry
    registry_path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    result_metrics = train()
    print(result_metrics)
    update_registry(result_metrics)
