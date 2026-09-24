"""
Trains the real species classifier that replaces the ImageNet-heuristic species-mismatch
check. See docs/specs/species-classifier.md and app/models/species_classifier.py's docstring
for why. Run from ml-service/ (venv active, torch/torchvision installed):

    python -m training.species_classifier_train

Same feature-extraction-once + linear-head-fine-tune approach as
training/cat_image_model_train.py — see that file's docstring for the full rationale.

Unlike the per-disease trainers, this one pulls from **multiple existing data directories**,
one per species, reusing photos already downloaded for the disease classifiers rather than
fetching anything new. Dog uses **both** its current (v2, skin close-up) and superseded (v1,
whole-body) photo sets combined — deliberately, so the classifier learns to recognize a dog
from a skin lesion close-up too, not just a whole-body photo. That's the exact gap that broke
the old ImageNet-heuristic approach for Dog specifically.
"""
from __future__ import annotations

import random
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.metrics import confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from torch import nn
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2

from app.models.image_model import PREPROCESS, build_model
from app.models.species_classifier import SPECIES

DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "species_classifier.pt"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "models" / "REGISTRY.md"

# species -> list of directories (searched recursively for images) that hold real photos of it.
SPECIES_TO_DATA_DIRS = {
    "CAT": [DATA_ROOT / "cat-images"],
    "COW": [DATA_ROOT / "cattle-images"],
    "DOG": [DATA_ROOT / "dog-images", DATA_ROOT / "dog-images-v1-superseded"],
    "GOAT": [DATA_ROOT / "goat-images"],
}

VAL_FRACTION = 0.2
HEAD_EPOCHS = 30
HEAD_LR = 1e-3
SEED = 42


def load_image_paths() -> tuple[list[Path], list[str]]:
    paths: list[Path] = []
    labels: list[str] = []
    for species, data_dirs in SPECIES_TO_DATA_DIRS.items():
        for data_dir in data_dirs:
            for image_path in sorted(data_dir.rglob("*")):
                if image_path.suffix.lower() in (".jpg", ".jpeg", ".png"):
                    paths.append(image_path)
                    labels.append(species)
    return paths, labels


def _extract_features(paths: list[Path], backbone: nn.Module) -> tuple[np.ndarray, list[int]]:
    """One frozen-backbone forward pass per image, batched. Corrupt/unreadable files are
    skipped with a warning rather than crashing the whole training run."""
    features = []
    batch: list[torch.Tensor] = []
    batch_indices: list[int] = []
    good_indices: list[int] = []

    def flush():
        if not batch:
            return
        with torch.no_grad():
            stacked = torch.stack(batch)
            pooled = backbone.features(stacked)
            pooled = nn.functional.adaptive_avg_pool2d(pooled, 1).flatten(1)
        features.extend(pooled.numpy())
        good_indices.extend(batch_indices)
        batch.clear()
        batch_indices.clear()

    for i, path in enumerate(paths):
        try:
            image = Image.open(path).convert("RGB")
            batch.append(PREPROCESS(image))
            batch_indices.append(i)
        except Exception as exc:  # noqa: BLE001 - dataset hygiene, not a code-path we branch on
            print(f"WARNING: skipping unreadable image {path}: {exc}")
            continue

        if len(batch) >= 64:
            flush()
    flush()

    return np.stack(features), good_indices


def train(model_path: Path = MODEL_PATH) -> dict:
    random.seed(SEED)
    torch.manual_seed(SEED)

    paths, labels = load_image_paths()
    if not paths:
        raise FileNotFoundError(f"No images found under {DATA_ROOT} — see per-species SOURCE.md files.")

    label_to_idx = {name: i for i, name in enumerate(SPECIES)}

    pretrained = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)
    pretrained.eval()
    for param in pretrained.parameters():
        param.requires_grad = False

    print(f"Extracting features for {len(paths)} images (one frozen-backbone pass)...")
    features, good_indices = _extract_features(paths, pretrained)
    y_raw = [labels[i] for i in good_indices]
    y = np.array([label_to_idx[label] for label in y_raw])
    dropped = len(paths) - len(good_indices)
    if dropped:
        print(f"WARNING: dropped {dropped} unreadable image(s) out of {len(paths)}")

    x_train, x_val, y_train, y_val = train_test_split(
        features, y, test_size=VAL_FRACTION, stratify=y, random_state=SEED
    )

    # Class-weighted loss: COW has 3244 real photos against DOG's 724 (~4.5x), and an
    # unweighted loss let that imbalance bias the model toward COW — confirmed the hard way,
    # not assumed: an unweighted first pass measured real Dog "Healthy" photos scoring higher
    # on COW than DOG (e.g. COW=0.68 vs DOG=0.11), which fed straight into the species-mismatch
    # check, false-rejecting genuine Dog submissions far more than intended. Inverse-frequency
    # weighting (computed from the actual training split, not the raw class counts, so it
    # reflects what the model really sees) corrects for this without discarding any real data.
    class_counts = np.bincount(y_train, minlength=len(SPECIES))
    class_weights = torch.tensor(len(y_train) / (len(SPECIES) * class_counts), dtype=torch.float32)
    print("Class weights:", dict(zip(SPECIES, [round(float(w), 3) for w in class_weights])))

    head = nn.Linear(pretrained.last_channel, len(SPECIES))
    optimizer = torch.optim.Adam(head.parameters(), lr=HEAD_LR)
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)

    x_train_t = torch.tensor(x_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    x_val_t = torch.tensor(x_val, dtype=torch.float32)

    for epoch in range(HEAD_EPOCHS):
        head.train()
        optimizer.zero_grad()
        logits = head(x_train_t)
        loss = loss_fn(logits, y_train_t)
        loss.backward()
        optimizer.step()
        if epoch == 0 or (epoch + 1) % 10 == 0:
            print(f"  epoch {epoch + 1}/{HEAD_EPOCHS}  loss={loss.item():.4f}")

    head.eval()
    with torch.no_grad():
        val_probs = torch.softmax(head(x_val_t), dim=1).numpy()
    val_preds = val_probs.argmax(axis=1)

    accuracy = float((val_preds == y_val).mean())
    f1_macro = float(f1_score(y_val, val_preds, average="macro"))
    per_class_f1 = f1_score(y_val, val_preds, average=None, labels=range(len(SPECIES)), zero_division=0)
    cm = confusion_matrix(y_val, val_preds, labels=range(len(SPECIES)))

    print(f"\nValidation accuracy: {accuracy:.3f}  macro F1: {f1_macro:.3f}")
    print("Per-class F1:", dict(zip(SPECIES, [round(float(f), 3) for f in per_class_f1])))
    print("Confusion matrix (rows=true, cols=predicted), order:", SPECIES)
    print(cm)

    # For picking a mismatch decision rule: how confident is the model in the TRUE class, and
    # in the best WRONG class, on validation data it never trained on.
    true_class_probs = val_probs[np.arange(len(y_val)), y_val]
    wrong_probs = val_probs.copy()
    wrong_probs[np.arange(len(y_val)), y_val] = 0.0
    best_wrong_probs = wrong_probs.max(axis=1)
    print(f"True-class prob: median={np.median(true_class_probs):.3f}  p10={np.percentile(true_class_probs, 10):.3f}")
    print(f"Best-wrong-class prob: median={np.median(best_wrong_probs):.3f}  p90={np.percentile(best_wrong_probs, 90):.3f}")

    final_model = build_model(len(SPECIES))
    pretrained_state = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1).state_dict()
    backbone_state = {k: v for k, v in pretrained_state.items() if not k.startswith("classifier.1.")}
    final_model.load_state_dict(backbone_state, strict=False)
    final_model.classifier[1].load_state_dict(head.state_dict())

    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(final_model.state_dict(), model_path)

    return {
        "n_samples": len(y),
        "n_train": len(y_train),
        "n_val": len(y_val),
        "class_distribution": {name: int((np.array(y_raw) == name).sum()) for name in SPECIES},
        "val_accuracy": accuracy,
        "val_f1_macro": f1_macro,
        "val_f1_per_class": dict(zip(SPECIES, [round(float(f), 4) for f in per_class_f1])),
    }


def update_registry(metrics: dict, model_path: Path = MODEL_PATH, registry_path: Path = REGISTRY_PATH) -> None:
    entry = (
        f"| `{model_path.name}` | species identity (CAT/COW/DOG/GOAT), not a disease — "
        f"replaces the ImageNet-heuristic species-mismatch check | "
        f"cat/cattle/dog(+v1)/goat-images combined ({metrics['n_samples']} images) | "
        f"acc={metrics['val_accuracy']:.3f}, f1_macro={metrics['val_f1_macro']:.3f} | "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')} |\n"
    )
    text = registry_path.read_text(encoding="utf-8")
    registry_path.write_text(text + entry, encoding="utf-8")


if __name__ == "__main__":
    result_metrics = train()
    print(result_metrics)
    update_registry(result_metrics)
