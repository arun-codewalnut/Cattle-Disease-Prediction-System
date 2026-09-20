"""
Trains the M9 real cattle image classifier.

See docs/specs/M9-cattle-image-classifier.md. Run from ml-service/ (venv active, torch/
torchvision installed):

    python -m training.image_model_train

Approach: transfer learning on a pretrained MobileNetV2 backbone, **frozen** — fine-tuning
only the classifier head. Deliberate implementation choice (documented, not hidden): rather
than running the frozen backbone forward on every image on every epoch, this extracts each
image's 1280-dim pooled feature vector once, then trains the head on the cached features —
computationally equivalent to fine-tuning a frozen-backbone model epoch after epoch (the
backbone's output for a given image never changes since it's frozen and not augmented), but
CPU-feasible in a fraction of the time. The saved artifact is still the full backbone + head
state_dict, so app/models/image_model.py's inference path doesn't know or care how it was
trained.
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

from app.models.image_model import DISEASES, PREPROCESS, build_model

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "cattle-images"
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "image_model.pt"
REGISTRY_PATH = Path(__file__).resolve().parents[1] / "models" / "REGISTRY.md"

# Folder name (as the Kaggle dataset ships it) -> canonical DISEASES label.
FOLDER_TO_DISEASE = {
    "healthy": "Healthy",
    "lumpy": "Lumpy Skin Disease",
    "foot-and-mouth": "Foot and Mouth Disease",
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


def _extract_features(paths: list[Path], backbone: nn.Module) -> np.ndarray:
    """One frozen-backbone forward pass per image, batched. Corrupt/unreadable files (if
    any slipped into the dataset) are skipped with a warning rather than crashing the whole
    training run."""
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


def train(data_path: Path = DATA_PATH, model_path: Path = MODEL_PATH) -> dict:
    random.seed(SEED)
    torch.manual_seed(SEED)

    paths, labels = load_image_paths(data_path)
    if not paths:
        raise FileNotFoundError(f"No images found under {data_path} — see SOURCE.md to populate it.")

    label_to_idx = {name: i for i, name in enumerate(DISEASES)}

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

    final_model = build_model()
    pretrained_state = mobilenet_v2(weights=MobileNet_V2_Weights.IMAGENET1K_V1).state_dict()
    # classifier.1.* is the original 1000-class ImageNet head — shape-incompatible with our
    # 3-class head, drop it here and load the fine-tuned head explicitly below instead.
    backbone_state = {k: v for k, v in pretrained_state.items() if not k.startswith("classifier.1.")}
    final_model.load_state_dict(backbone_state, strict=False)
    final_model.classifier[1].load_state_dict(head.state_dict())

    model_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(final_model.state_dict(), model_path)

    return {
        "n_samples": len(y),
        "n_train": len(y_train),
        "n_val": len(y_val),
        "class_distribution": {name: int((np.array(y_raw) == name).sum()) for name in DISEASES},
        "val_accuracy": accuracy,
        "val_f1_macro": f1_macro,
        "val_f1_per_class": dict(zip(DISEASES, [round(float(f), 4) for f in per_class_f1])),
    }


def update_registry(metrics: dict, model_path: Path = MODEL_PATH, registry_path: Path = REGISTRY_PATH) -> None:
    entry = (
        f"| `{model_path.name}` | Healthy / Lumpy Skin Disease / Foot and Mouth Disease "
        f"(not Mastitis/BRD) | cattle-images ({metrics['n_samples']} images) | "
        f"acc={metrics['val_accuracy']:.3f}, f1_macro={metrics['val_f1_macro']:.3f} | "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')} |\n"
    )
    text = registry_path.read_text(encoding="utf-8")
    registry_path.write_text(text + entry, encoding="utf-8")


if __name__ == "__main__":
    result_metrics = train()
    print(result_metrics)
    update_registry(result_metrics)
