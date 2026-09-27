# Dataset: goat-images

**Real photographs, not synthetic** — used for the Goat image classifier (M16, see
`docs/specs/M16-goat-disease-detection.md`).

## Source

[Healthy and Unhealthy Goat Images](https://www.kaggle.com/datasets/kartikeybartwal/dataset)
(Kaggle, `kartikeybartwal`), downloaded via `kagglehub.dataset_download(...)` — no Kaggle
account/API token required for this public dataset.

## Classes

927 usable images (one file failed to decode and is skipped by the training script), 2
classes — folder name -> `DISEASES` label in `app/models/goat_image_model.py`:

| Folder | `DISEASES` label | Images |
|---|---|---|
| `healthy/` | `Healthy` | 439 |
| `unhealthy/` | `Unhealthy` | 488 |

**This is binary Healthy/Unhealthy only — no disease-specific goat image dataset was found**
in this session's search (queries tried: "goat disease", "goat skin disease", "goat pox",
"goat images" against the public Kaggle search API). This is a materially different, more
limited capability than Cat's or Dog's models: a Goat image diagnosis can say a photo looks
off, but **never names what's wrong** — there is no disease class for it to predict. Disclosed
in the frontend and `docs/DISCLAIMER.md`, not just here.

## License

**Apache 2.0** — confirmed via the Kaggle public API's `licenseName` field, a clearer bar than
several earlier datasets in this project that shipped with no listed license.

## Redownload

```python
import kagglehub
path = kagglehub.dataset_download("kartikeybartwal/dataset")
```

Then copy `healthy_goat/` and `unhealthy_goat/` into this directory as `healthy/` and
`unhealthy/`.
