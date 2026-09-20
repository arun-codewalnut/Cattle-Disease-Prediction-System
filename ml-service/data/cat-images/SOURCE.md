# Dataset: cat-images

**Real photographs, not synthetic** — used for the Cat image classifier (M13 follow-up, see
`docs/specs/M13-cat-disease-detection.md`).

## Source

[Cat Skin Disease](https://www.kaggle.com/datasets/nofalrafif/cat-skin-disease) (Kaggle,
`nofalrafif`), downloaded via `kagglehub.dataset_download(...)` — no Kaggle account/API token
required for this public dataset.

## Classes

1,000 images total, 4 balanced classes (250 each) — folder name → `DISEASES` label in
`app/models/cat_image_model.py`:

| Folder | `DISEASES` label | Images |
|---|---|---|
| `flea-allergy/` | `Flea Allergy` | 250 |
| `healthy/` | `Healthy` | 250 |
| `ringworm/` | `Ringworm` | 250 |
| `scabies/` | `Scabies` | 250 |

**This replaces the disease list M13 originally researched** (Feline Upper Respiratory
Infection, Ringworm, FIV) — no image data exists for URI or FIV in anything found this session.
Ringworm carries over; Flea Allergy and Scabies are new, Healthy is new. See the "Follow-up"
section in `docs/specs/M13-cat-disease-detection.md` for why the list changed.

A separate dataset (`smadive/pet-disease-images`, see `../dog-images/SOURCE.md` for its Dog
half) has 11 more Cat-specific disease classes (Feline Leukemia, Feline Panleukopenia, Dental
Disease, Ear Mites, Eye Infection, Fungal Infection, Skin Allergy, UTI, Worm Infection, plus
its own Ringworm/Scabies folders) but **no Cat-Healthy photos** — not used this round, flagged
as available follow-up if a future session wants a richer Cat model.

## License

**Not verified** — same honesty bar as `cattle-images/SOURCE.md`; check the
[Kaggle listing](https://www.kaggle.com/datasets/nofalrafif/cat-skin-disease) directly before
any redistribution beyond this project's own local training use.

## Redownload

```python
import kagglehub
path = kagglehub.dataset_download("nofalrafif/cat-skin-disease")
```

Then copy `CAT SKIN DISEASE/{Flea_Allergy,Health,Ringworm,Scabies}/` into this directory as
`{flea-allergy,healthy,ringworm,scabies}/`.
