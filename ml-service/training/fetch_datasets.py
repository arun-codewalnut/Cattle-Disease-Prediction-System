"""
Downloads every Kaggle training dataset and lays it out under data/ exactly as the training
scripts expect — one command instead of following each data/*/SOURCE.md by hand. The folder
renames below are the ones those SOURCE.md files document.

Run from ml-service/ (kagglehub is installed by requirements.txt):

    python -m training.fetch_datasets

No Kaggle account or API token needed. About 800MB of downloads; kagglehub caches them under
~/.cache/kagglehub, so a re-run doesn't download again. A target folder that already has
files is skipped, never overwritten — delete it first to re-copy.

Not covered:
- Cow Mastitis photos (data/cattle-images/mastitis/) need a Roboflow API key and a manual
  review pass a script can't do — see training/fetch_mastitis_data.py and
  data/cattle-images/SOURCE.md.
- The Cow symptom dataset isn't downloaded at all; training.generate_synthetic_data creates it.

The datasets are only needed to retrain models or run the real-photo tests — the app itself
runs on the committed model files in models/.
"""
from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# OS clutter that can sit inside a cached download (Windows Explorer writes desktop.ini into
# folders it has displayed) — never part of a dataset.
_IGNORED_FILES = shutil.ignore_patterns("desktop.ini", "Thumbs.db", ".DS_Store")

# (Kaggle id, {path inside the download: target path under data/}). Paths inside the download
# are relative to the version root kagglehub returns — checked against real downloads.
DATASETS: list[tuple[str, dict[str, str]]] = [
    (
        "devang03mgr/cattle-diseases-datasets",
        {
            "Cows datasets/healthy": "cattle-images/healthy",
            "Cows datasets/lumpy": "cattle-images/lumpy",
            "Cows datasets/foot-and-mouth": "cattle-images/foot-and-mouth",
        },
    ),
    (
        "nofalrafif/cat-skin-disease",
        {
            "CAT SKIN DISEASE/Flea_Allergy": "cat-images/flea-allergy",
            "CAT SKIN DISEASE/Health": "cat-images/healthy",
            "CAT SKIN DISEASE/Ringworm": "cat-images/ringworm",
            "CAT SKIN DISEASE/Scabies": "cat-images/scabies",
        },
    ),
    (
        "yashmotiani/dogs-skin-disease-dataset",
        {
            "Dogs/Bacterial_dermatosis": "dog-images/bacterial-dermatosis",
            "Dogs/Fungal_infections": "dog-images/fungal-infection",
            "Dogs/Healthy": "dog-images/healthy",
            "Dogs/Hypersensitivity_allergic_dermatosis": "dog-images/hypersensitivity-allergic-dermatosis",
        },
    ),
    (
        "kartikeybartwal/dataset",
        {
            "healthy_goat": "goat-images/healthy",
            "unhealthy_goat": "goat-images/unhealthy",
        },
    ),
    (
        "devothanyambo/ppr-disease-data-from-goats-and-sheep",
        {"PPR-Goats-Sheep.csv": "sheep-symptoms/PPR-Goats-Sheep.csv"},
    ),
]


def _already_present(dest: Path) -> bool:
    if dest.is_file():
        return True
    return dest.is_dir() and any(dest.iterdir())


def _long(path: Path) -> str:
    # Some Kaggle filenames are 150+ characters, which can push a full path past Windows'
    # 260-character limit. The \\?\ prefix lifts that limit for these copies.
    if os.name == "nt":
        return "\\\\?\\" + str(path.resolve())
    return str(path)


def _copy_dir(src: Path, dest: Path) -> None:
    # Copy into a sibling ".partial" folder and rename only once it's complete, so a copy that
    # fails halfway never looks "already present" to _already_present() on the next run.
    partial = dest.with_name(dest.name + ".partial")
    shutil.rmtree(_long(partial), ignore_errors=True)
    shutil.copytree(_long(src), _long(partial), ignore=_IGNORED_FILES)
    if dest.exists():  # an empty leftover folder — _already_present() said it has no files
        dest.rmdir()
    partial.rename(dest)


def fetch_all(data_dir: Path = DEFAULT_DATA_DIR) -> None:
    import kagglehub  # imported here so --help works even before requirements are installed

    for kaggle_id, mapping in DATASETS:
        pending = {src: data_dir / target for src, target in mapping.items()}
        pending = {src: dest for src, dest in pending.items() if not _already_present(dest)}
        if not pending:
            print(f"[skip] {kaggle_id}: already downloaded")
            continue

        root = Path(kagglehub.dataset_download(kaggle_id))
        print(f"[get ] {kaggle_id}")
        for src_rel, dest in pending.items():
            src = root / src_rel
            if not src.exists():
                raise FileNotFoundError(
                    f"{kaggle_id}: expected '{src_rel}' in the download at {root} — the dataset's "
                    "layout may have changed; check its data/*/SOURCE.md"
                )
            dest.parent.mkdir(parents=True, exist_ok=True)
            shown = f"data/{dest.relative_to(data_dir).as_posix()}"
            if src.is_dir():
                _copy_dir(src, dest)
                # Counted through the long-path form too, or the longest filenames are missed.
                count = sum(1 for entry in os.scandir(_long(dest)) if entry.is_file())
                print(f"       {src_rel} -> {shown} ({count} files)")
            else:
                shutil.copy2(src, dest)
                print(f"       {src_rel} -> {shown}")

    print("\nDone. Cow Mastitis photos aren't included - see training/fetch_mastitis_data.py.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download the Kaggle training datasets into data/ (see this module's docstring)."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="where to put the datasets (default: ml-service/data)",
    )
    fetch_all(parser.parse_args().data_dir)
