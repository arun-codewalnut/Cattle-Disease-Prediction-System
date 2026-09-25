"""
One-off script: downloads the cow-and-mastitis-detection dataset (Roboflow Universe,
kirubel-yemane, CC BY 4.0) and converts its Mastitis_infected_udder-annotated images into
this project's whole-image, folder-per-class convention (data/cattle-images/mastitis/). See
docs/specs/cow-mastitis-image-classifier.md for the full rationale.

Run once from ml-service/ (venv active, ROBOFLOW_API_KEY set in .env — never pass it on the
command line or print it):

    python -m training.fetch_mastitis_data

Uses dataset version 1 deliberately, not a later one: v1 is the only version confirmed (via
its own Roboflow page) to have "No augmentations were applied" — 790 raw images. Later
versions mix in synthetic augmentation (rotation/flip/etc. duplicates of the same underlying
photos), which would inflate the apparent dataset size without adding real information, the
same "don't train on inflated/duplicated data" standard this project already applies elsewhere
(see species_classifier.py's class-weighting fix). If v1's real Mastitis-labeled count turns
out too small to train on, that's a decision to revisit deliberately, not a default to drift
into by grabbing the biggest version available.

This only ever ADDS to data/cattle-images/mastitis/ — it never touches the existing
healthy/lumpy/foot-and-mouth folders.
"""
from __future__ import annotations

import os
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

DATASET_VERSION = 1
WORKSPACE = "kirubel-yemane"
PROJECT = "cow-and-mastitis-detection"

# v1's real annotation classes turned out to differ from the project overview page's
# (capitalized, thermal-free) list — verified by actually downloading and parsing v1's XML,
# not assumed from the page. v1 uses lowercase names and additionally has several
# "thermal_*" classes (infrared-camera images) alongside the regular-photo ones. Matched
# case-insensitively so a naming variant doesn't silently zero out the count again; any image
# ALSO carrying a thermal_* label is excluded even if it also has the target class, since a
# thermal/false-color image is a different visual domain than the regular phone photos this
# classifier is otherwise trained and used on — mixing them in would teach the model a
# spurious "mastitis looks like this heat-map" signal no real submitted photo would ever match.
TARGET_CLASS = "mastitis_infected_udder"

RAW_EXPORT_DIR = Path(__file__).resolve().parents[1] / "data" / "_mastitis_raw_export"
TARGET_DIR = Path(__file__).resolve().parents[1] / "data" / "cattle-images" / "mastitis"


def download() -> Path:
    import roboflow

    api_key = os.environ.get("ROBOFLOW_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ROBOFLOW_API_KEY not set. Add it to ml-service/.env — see "
            "docs/specs/cow-mastitis-image-classifier.md."
        )

    rf = roboflow.Roboflow(api_key=api_key)
    project = rf.workspace(WORKSPACE).project(PROJECT)
    dataset = project.version(DATASET_VERSION).download("voc", location=str(RAW_EXPORT_DIR))
    return Path(dataset.location)


def _classes_in(xml_path: Path) -> set[str]:
    tree = ET.parse(xml_path)
    return {obj.findtext("name") for obj in tree.getroot().findall("object")}


def _find_image(xml_path: Path) -> Path | None:
    for ext in (".jpg", ".jpeg", ".png"):
        candidate = xml_path.with_suffix(ext)
        if candidate.exists():
            return candidate
    return None


def convert(export_dir: Path) -> dict:
    """Copies (not crops) every image with >=1 mastitis_infected_udder box into TARGET_DIR —
    matched case-insensitively, and skipped if the same image also carries any thermal_*
    label (see TARGET_CLASS's comment). Also reports the full per-class distribution across
    every annotation found, so a human can sanity-check the real class balance before training
    on it — not just take the mastitis count on faith."""
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    class_counts: dict[str, int] = {}
    copied = 0
    excluded_thermal = 0
    parse_errors = 0
    missing_images = 0

    xml_paths = sorted(export_dir.rglob("*.xml"))
    for xml_path in xml_paths:
        try:
            classes = _classes_in(xml_path)
        except ET.ParseError:
            parse_errors += 1
            continue

        for cls in classes:
            class_counts[cls] = class_counts.get(cls, 0) + 1

        classes_lower = {c.lower() for c in classes if c}
        if TARGET_CLASS not in classes_lower:
            continue
        if any(c.startswith("thermal_") for c in classes_lower):
            excluded_thermal += 1
            continue

        image_path = _find_image(xml_path)
        if image_path is None:
            missing_images += 1
            continue

        shutil.copy2(image_path, TARGET_DIR / image_path.name)
        copied += 1

    return {
        "total_annotation_files": len(xml_paths),
        "class_counts": class_counts,
        "mastitis_images_copied": copied,
        "excluded_thermal": excluded_thermal,
        "parse_errors": parse_errors,
        "missing_images": missing_images,
    }


if __name__ == "__main__":
    print(f"Downloading {WORKSPACE}/{PROJECT} v{DATASET_VERSION} (Pascal VOC)...")
    export_path = download()
    print(f"Exported to {export_path}")

    result = convert(export_path)
    print(f"\nAnnotation files scanned: {result['total_annotation_files']}")
    print(f"Class distribution across all annotations: {result['class_counts']}")
    print(f"\nCopied {result['mastitis_images_copied']} Mastitis-labeled image(s) into {TARGET_DIR}")
    if result["excluded_thermal"]:
        print(f"Excluded {result['excluded_thermal']} thermal/infrared-labeled image(s) — different visual domain, not used")
    if result["parse_errors"]:
        print(f"WARNING: {result['parse_errors']} annotation file(s) failed to parse")
    if result["missing_images"]:
        print(f"WARNING: {result['missing_images']} annotation(s) had no matching image file")
