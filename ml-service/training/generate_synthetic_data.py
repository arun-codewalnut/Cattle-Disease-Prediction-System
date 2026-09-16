"""
Generates the synthetic symptom -> disease dataset used to train the M1 baseline model.

See ml-service/data/synthetic-symptom-dataset/SOURCE.md for why this is synthetic rather
than a real public dataset, and how to regenerate it.
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

from app.models.symptom_model import DISEASES, FEATURES

# Per-disease probability that a given symptom is present. Hand-authored to be roughly
# realistic and clearly separable per class — not derived from real veterinary data.
DISEASE_PROFILES = {
    "Foot and Mouth Disease": {
        "fever": 0.85, "appetite_loss": 0.55, "nasal_discharge": 0.15,
        "milk_yield_drop": 0.3, "mouth_lesions": 0.9, "lameness": 0.6,
        "excessive_salivation": 0.8, "skin_nodules": 0.05, "udder_swelling": 0.05,
        "coughing": 0.1, "labored_breathing": 0.1,
    },
    "Lumpy Skin Disease": {
        "fever": 0.8, "appetite_loss": 0.5, "nasal_discharge": 0.1,
        "milk_yield_drop": 0.6, "mouth_lesions": 0.05, "lameness": 0.15,
        "excessive_salivation": 0.05, "skin_nodules": 0.9, "udder_swelling": 0.1,
        "coughing": 0.05, "labored_breathing": 0.1,
    },
    "Mastitis": {
        "fever": 0.4, "appetite_loss": 0.3, "nasal_discharge": 0.05,
        "milk_yield_drop": 0.85, "mouth_lesions": 0.02, "lameness": 0.1,
        "excessive_salivation": 0.02, "skin_nodules": 0.02, "udder_swelling": 0.9,
        "coughing": 0.02, "labored_breathing": 0.05,
    },
    "Bovine Respiratory Disease": {
        "fever": 0.7, "appetite_loss": 0.4, "nasal_discharge": 0.85,
        "milk_yield_drop": 0.3, "mouth_lesions": 0.02, "lameness": 0.05,
        "excessive_salivation": 0.1, "skin_nodules": 0.02, "udder_swelling": 0.05,
        "coughing": 0.85, "labored_breathing": 0.7,
    },
    "Healthy": {feature: 0.05 for feature in FEATURES},
}

MISSING_RATE = 0.08
SAMPLES_PER_CLASS = 150
DEFAULT_OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "symptom_dataset.csv"


def _generate_row(disease: str, rng: random.Random) -> dict[str, object]:
    profile = DISEASE_PROFILES[disease]
    row: dict[str, object] = {}
    for feature in FEATURES:
        if rng.random() < MISSING_RATE:
            row[feature] = ""  # empty cell = missing
        else:
            row[feature] = int(rng.random() < profile[feature])
    row["diagnosis"] = disease
    return row


def main(seed: int = 42, out_path: Path = DEFAULT_OUT_PATH) -> Path:
    rng = random.Random(seed)
    rows = [_generate_row(disease, rng) for disease in DISEASES for _ in range(SAMPLES_PER_CLASS)]
    rng.shuffle(rows)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[*FEATURES, "diagnosis"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")
    return out_path


if __name__ == "__main__":
    main()
