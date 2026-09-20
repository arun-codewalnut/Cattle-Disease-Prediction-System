"""
Trains the M14 follow-up real dog image classifier.

See docs/specs/M14-dog-disease-detection.md. Run from ml-service/ (venv active, torch/
torchvision installed):

    python -m training.dog_image_model_train

Same feature-extraction-once + linear-head-fine-tune approach as training/image_model_train.py
— see that file's docstring for the full rationale. Only the data path, disease list, and
folder mapping differ.

**No "Healthy" class** — see app/models/dog_image_model.py's docstring. The per-class counts
here are also genuinely imbalanced (58-82/class) — not padded to look even; the per-class F1
printed below is the honest signal for whether the smaller Distemper class is underserved.
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

from app.models.dog_image_model import DISEASES
from app.models.image_model import PREPROCESS, build_model

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "dog-images"
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "dog_image_model.pt"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "models" / "REGISTRY.md"

# Folder name (as the Kaggle dataset ships it) -> canonical DISEASES label.
FOLDER_TO_DISEASE = {
    "distemper": "Canine Distemper",
    "parvovirus": "Canine Parvovirus",
    "kennel-cough": "Kennel Cough",
    "mange": "Mange",
}

VAL_FRACTION = 0.2
HEAD_EPOCHS = 30
HEAD_LR = 1e-3
SEED = 42


def load_image_paths(data_path: Path = DATA_PATH) -> tuple[list[Path], list[str]]:
    paths: list[Path] = []
    labels: list[str] = []
    for folder_name, disease in FOLDER_TO_DISEASE.items():
        folder = data_path / folder_name
        for image_path in sorted(folder.glob("*")):
            if image_path.suffix.lower() in (".jpg", ".jpeg", ".png"):
                paths.append(image_path)
                labels.append(disease)
    return paths, labels


def _extract_features(
    paths: list[Path], backbone: nn.Module, augment: bool = False
) -> tuple[np.ndarray, list[int]]:
    """One frozen-backbone forward pass per image (two, if augment=True: original + a
    horizontal flip), batched. Corrupt/unreadable files (if any slipped into the dataset) are
    skipped with a warning rather than crashing the whole training run.

    `augment` exists because this dataset's smallest class (Canine Distemper, 56 images) is
    genuinely thin — flipping is applied only where the caller has already excluded the
    validation split, never to validation images themselves, so the reported metrics stay an
    honest read on unseen, unaugmented photos."""
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
            if augment:
                flipped = image.transpose(Image.FLIP_LEFT_RIGHT)
                batch.append(PREPROCESS(flipped))
                batch_indices.append(i)
        except Exception as exc:  # noqa: BLE001 - dataset hygiene, not a code-path we branch on
            print(f"WARNING: skipping unreadable image {path}: {exc}")
            continue

        if len(batch) >= 64:
            flush()
    flush()

    return np.stack(features), good_indices


def train(data_path: Path = DATA_PATH, model_path: Path = MODEL_PATH) -> dict:
    random.seed(SEED)
    torch.manual_seed(SEED)

    paths, labels = load_image_paths(data_path)
    if not paths:
        raise FileNotFoundError(f"No images found under {data_path} — see SOURCE.md to populate it.")

    label_to_idx = {name: i for i, name in enumerate(DISEASES)}
    y_all = np.array([label_to_idx[label] for label in labels])

    # Split at the photo level BEFORE any feature extraction/augmentation, so a flipped
    # training image can never leak information about its original into the validation set.
    train_paths, val_paths, y_train_raw, y_val = train_test_split(
        paths, y_all, test_size=VAL_FRACTION, stratify=y_all, random_state=SEED
    )

    pretrained = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1)
    pretrained.eval()
    for param in pretrained.parameters():
        param.requires_grad = False

    print(f"Extracting val features for {len(val_paths)} images (unaugmented)...")
    x_val, val_good = _extract_features(val_paths, pretrained, augment=False)
    y_val = y_val[val_good]

    print(f"Extracting train features for {len(train_paths)} images (+ horizontal-flip augmentation)...")
    x_train, train_good = _extract_features(train_paths, pretrained, augment=True)
    # good_indices has each successfully-processed source index twice (original + flipped, in
    # that order) — fancy-indexing y_train_raw with it lines labels up with x_train directly,
    # no separate repeat/dedup logic needed.
    y_train = y_train_raw[train_good]

    dropped = len(train_paths) - len(set(train_good)) + len(val_paths) - len(val_good)
    if dropped:
        print(f"WARNING: dropped {dropped} unreadable image(s) out of {len(paths)}")

    head = nn.Linear(pretrained.last_channel, len(DISEASES))
    optimizer = torch.optim.Adam(head.parameters(), lr=HEAD_LR)
    loss_fn = nn.CrossEntropyLoss()

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
        val_preds = torch.argmax(head(x_val_t), dim=1).numpy()

    accuracy = float((val_preds == y_val).mean())
    f1_macro = float(f1_score(y_val, val_preds, average="macro"))
    per_class_f1 = f1_score(y_val, val_preds, average=None, labels=range(len(DISEASES)), zero_division=0)
    cm = confusion_matrix(y_val, val_preds, labels=range(len(DISEASES)))

    print(f"\nValidation accuracy: {accuracy:.3f}  macro F1: {f1_macro:.3f}")
    print("Per-class F1:", dict(zip(DISEASES, [round(float(f), 3) for f in per_class_f1])))
    print("Confusion matrix (rows=true, cols=predicted), order:", DISEASES)
    print(cm)

    final_model = build_model(len(DISEASES))
    pretrained_state = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1).state_dict()
    # classifier.1.* is the original 1000-class ImageNet head — shape-incompatible with our
    # head, drop it here and load the fine-tuned head explicitly below instead.
    backbone_state = {k: v for k, v in pretrained_state.items() if not k.startswith("classifier.1.")}
    final_model.load_state_dict(backbone_state, strict=False)
    final_model.classifier[1].load_state_dict(head.state_dict())

    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(final_model.state_dict(), model_path)

    return {
        "n_samples": len(paths),
        "n_train": len(train_paths),
        "n_train_augmented": len(x_train),
        "n_val": len(y_val),
        "class_distribution": {name: labels.count(name) for name in DISEASES},
        "val_accuracy": accuracy,
        "val_f1_macro": f1_macro,
        "val_f1_per_class": dict(zip(DISEASES, [round(float(f), 4) for f in per_class_f1])),
    }


def update_registry(metrics: dict, model_path: Path = MODEL_PATH, registry_path: Path = REGISTRY_PATH) -> None:
    entry = (
        f"| `{model_path.name}` | Canine Distemper / Canine Parvovirus / Kennel Cough / Mange "
        f"(no Healthy class — see SOURCE.md) | dog-images ({metrics['n_samples']} images) | "
        f"acc={metrics['val_accuracy']:.3f}, f1_macro={metrics['val_f1_macro']:.3f} | "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')} |\n"
    )
    text = registry_path.read_text(encoding="utf-8")
    registry_path.write_text(text + entry, encoding="utf-8")


if __name__ == "__main__":
    result_metrics = train()
    print(result_metrics)
    update_registry(result_metrics)
