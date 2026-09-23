# Dataset: dog-images

**Real photographs, not synthetic** — used for the Dog image classifier.

## v2 (current) — M16 follow-up, see `docs/specs/M14-dog-disease-detection.md`

**This replaces the v1 dataset below.** The v1 model (52.6% accuracy, 0.489 macro F1, no
Healthy class, 0.25 F1 for Canine Distemper specifically — worse than random) was flagged in
`docs/DECISIONS.md`/`STATE.md` as a candidate for replacement. A fresh Kaggle search this
session found a real classification-ready dataset covering **skin** diseases instead of the
v1 list's systemic ones — the same kind of shift that got Cat's model to 83% (M13's
skin-disease list vs. its original systemic-disease research).

### Source

[Dogs Skin disease dataset](https://www.kaggle.com/datasets/yashmotiani/dogs-skin-disease-dataset)
(Kaggle, `yashmotiani`), downloaded via `kagglehub.dataset_download(...)` — no Kaggle
account/API token required.

### Classes

439 images total, 4 classes (unbalanced — real data, not padded to match) — folder name ->
`DISEASES` label in `app/models/dog_image_model.py`:

| Folder | `DISEASES` label | Images |
|---|---|---|
| `bacterial-dermatosis/` | `Bacterial Dermatosis` | 94 |
| `fungal-infection/` | `Fungal Infection` | 137 |
| `healthy/` | `Healthy` | 119 |
| `hypersensitivity-allergic-dermatosis/` | `Hypersensitivity/Allergic Dermatosis` | 89 |

**Has a real `Healthy` class** — the v1 dog model's most-flagged gap, gone.

### Same source, richer classes not used this round

The same Roboflow project (`litespy-l22hu/dog-skin-diseases`) is also mirrored, in YOLO
object-detection format, inside a second Kaggle dataset
(`diemhuongnt12/5-skin-dog-diseases`, `dataset2/`) with the identical 4 classes — confirmed
by matching class names, so it's the same underlying data, not new signal. That same Kaggle
dataset's `dataset1/` is a **different** Roboflow project
(`canine-project/canine-qhgnq`, CC BY 4.0) covering **demodicosis** and **ringworm** — two
disease classes not in this model at all. Not used this round: it's YOLO-detection-formatted
(bounding boxes, not a plain classification split) and Roboflow exports commonly include
augmented duplicates of the same source photo across splits, which risks inflating validation
accuracy through train/val leakage unless carefully deduplicated first — flagged as a real
follow-up if Dog's disease coverage is revisited, not silently mixed in here.

### License

**CC0: Public Domain** — confirmed via the Kaggle public API's `licenseName` field.

### Redownload

```python
import kagglehub
path = kagglehub.dataset_download("yashmotiani/dogs-skin-disease-dataset")
```

Then copy `Dogs/{Bacterial_dermatosis,Fungal_infections,Healthy,Hypersensitivity_allergic_dermatosis}/`
into this directory as `{bacterial-dermatosis,fungal-infection,healthy,hypersensitivity-allergic-dermatosis}/`.

## v1 (superseded) — M14 follow-up

Moved to `data/dog-images-v1-superseded/` rather than deleted, per this repo's "supersede,
don't overwrite" convention (normally applied to `docs/DECISIONS.md`, extended here since the
artifact itself changed). Not used by any current code path.

[Pet Disease images](https://www.kaggle.com/datasets/smadive/pet-disease-images) (Kaggle,
`smadive`). 293 images, 4 classes: `distemper/` -> `Canine Distemper` (58),
`parvovirus/` -> `Canine Parvovirus` (82), `kennel-cough/` -> `Kennel Cough` (82),
`mange/` -> `Mange` (71). No Healthy photos existed in this dataset or anything else found
across any session at the time. License not verified.
