# Dataset: cattle-images

**Real photographs, not synthetic** — used for the M9 image classifier
(`docs/specs/M9-cattle-image-classifier.md`).

## Source

[Cattle Diseases Datasets](https://www.kaggle.com/datasets/devang03mgr/cattle-diseases-datasets)
(Kaggle, `devang03mgr`), downloaded via `kagglehub.dataset_download(...)` — no Kaggle
account/API token was required for this public dataset.

## Classes

3,244 images total, 3 classes (folder name → `DISEASES` label in
`app/models/image_model.py`):

| Folder | `DISEASES` label | Images |
|---|---|---|
| `healthy/` | `Healthy` | 1,291 |
| `lumpy/` | `Lumpy Skin Disease` | 1,207 |
| `foot-and-mouth/` | `Foot and Mouth Disease` | 746 |

`Mastitis` and `Bovine Respiratory Disease` — 2 of the symptom model's 5 classes — are **not**
covered by this dataset or the image classifier trained on it. Don't imply parity with the
symptom model's coverage anywhere this is referenced.

## License

**Not verified** — the Kaggle dataset page is JS-rendered, so automated fetch couldn't confirm
a license during this session. Flagged, not silently assumed; check the
[Kaggle listing](https://www.kaggle.com/datasets/devang03mgr/cattle-diseases-datasets) directly
before any redistribution beyond this project's own local training use.

## Redownload

```python
import kagglehub
path = kagglehub.dataset_download("devang03mgr/cattle-diseases-datasets")
```

Then copy the `Cows datasets/{healthy,lumpy,foot-and-mouth}/` subfolders into this directory.

## `mastitis/` — a second, separate source (2026-09-24)

See `docs/specs/cow-mastitis-image-classifier.md`. **Real photographs, manually curated — not
a straight bulk import.**

### Source

[cow-and-mastitis-detection](https://universe.roboflow.com/kirubel-yemane/cow-and-mastitis-detection)
(Roboflow Universe, `kirubel-yemane`), dataset **version 1** specifically (790 images,
"No augmentations were applied" per its own version page — later versions add synthetic
augmentation duplicates). Object-detection annotated (Pascal VOC); this project only needs
whole-image classification, so the raw export was converted via
`training/fetch_mastitis_data.py`: any image with >=1 `mastitis_infected_udder` box (matched
case-insensitively; the project's own class list is capitalized differently, see that script's
comments) was copied whole, excluding anything also carrying a `thermal_*` label (infrared
images — a different visual domain than a phone photo).

### License and a real, disclosed data-quality problem found during curation

**Listed as CC BY 4.0**, but **do not take that at face value for this folder** — manual
review (opening every one of the 319 initially-matched images, not just a sample) found the
dataset's "online sources" component (per its own description: "4803 different images from
Ethiopia dairy farms and online sources") includes images that plainly aren't originals:
- Several carry visible **iStock** or **Shutterstock** watermarks (i.e., they're scraped stock
  photography, not the uploader's own work, regardless of the CC BY 4.0 label on the dataset
  as a whole).
- At least 3 are **not cattle at all** — close-up photos of a human hand/finger, one of them
  showing a "closed captions" watermark indicating it's a video screen-grab.
- One has a book/publication cover banner baked into the image; another has an
  academic-figure-style label box — both suggest copied-from-a-publication, not original
  photography.

12 confirmed-bad images (of 48 initially matched under the `Mastitis-N-*` naming pattern) were
excluded for exactly these reasons. **Residual risk, disclosed and accepted, not hidden**: the
remaining images don't show a visible watermark, but given how evenly the same naming/rotation
pattern was shared between the watermarked and unwatermarked files, it's plausible some of the
"clean" ones are also scraped and simply don't happen to show a watermark in this particular
crop. Used anyway, per an explicit decision to accept that residual risk rather than discard
usable-looking data outright — revisit if a cleaner-provenance Mastitis dataset is ever found.

### Also found, and handled separately during curation

- **Deduplication**: the `Mastitis-N-*` files were not 140 distinct photos — Roboflow's export
  saved 3 differently-rotated crops per underlying photo (48 unique source images). Only the
  largest (by file size, a simple heuristic, not a perfect one) of each group of 3 was kept,
  to avoid the same underlying photo landing in both the train and validation split and
  inflating the measured accuracy.
- **The wider "online sources" bucket wasn't used at all**: dataset version 1 also had a
  second, much larger group of differently-named files (`Picture-N-400x284`, and various
  `*-400x284` filenames matching a teat-condition photo-atlas naming style, ~168 images) that
  turned out to be a genuinely mixed bag — some strong real mastitis photos, but also more
  wrong-species and watermarked images. Not curated or used this pass; a larger effort if
  ever revisited, not assumed to be free extra data.

### Composition

47 images total: 36 from the `Mastitis-N-*` group (post-dedup, post-exclusion) + 11 from a
distinct `IMG_2025...`/numbered-filename group (no quality issues found in that smaller
group). Meaningfully smaller than the other 3 classes in this folder (746-1291 images each) —
disclosed in `docs/DISCLAIMER.md`, not glossed over.

### Redownload

`roboflow` isn't in `requirements.txt` — same "on-demand, not a permanent app dependency"
convention as `kagglehub` for the other 3 classes' datasets. Install it, add
`ROBOFLOW_API_KEY` to `ml-service/.env` (a free Roboflow account's own API key — see its
account settings page), then:

```bash
pip install roboflow
python -m training.fetch_mastitis_data   # downloads + converts into this folder
```

Unlike the other 3 classes, **this is not a "just re-run it" pipeline** — re-running only
gets you back to the uncurated 319-image match, since the exclusions above were manual
judgment calls a script can't make. Re-review before trusting a fresh download.

Then re-run the conversion (`training.fetch_mastitis_data.convert`) and manually re-verify —
this is not a "just re-run it" pipeline; the curation step above found real problems that a
script alone would not have caught.
