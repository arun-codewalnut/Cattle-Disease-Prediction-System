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
