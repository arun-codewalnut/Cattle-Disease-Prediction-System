# Dataset: sheep-symptoms

**Real field-collected clinical data, not synthetic** (mostly) — used for the Sheep symptom
model (M12 follow-up, see `docs/specs/M12-sheep-disease-detection.md`).

## Source

[PPR disease data from goats and sheep](https://www.kaggle.com/datasets/devothanyambo/ppr-disease-data-from-goats-and-sheep)
(Kaggle, `devothanyambo`), downloaded via `kagglehub.dataset_download(...)` — no Kaggle
account/API token required for this public dataset.

Clinical field data collected across 6 districts of Northern Tanzania (pastoralist
communities), with ground truth confirmed by **RT-qPCR lab test**, not just observed
symptoms — a real diagnostic signal, not self-report. Per the dataset's own description:
161 original samples, only 12 PPR-positive; the severe imbalance was corrected with CTGAN
synthetic data augmentation to ~21,199 rows (`result` class balance ≈ 64% positive / 36%
negative after augmentation — see training script output for the exact split actually used).

## What's actually usable — and what isn't

The file ships **fully pre-encoded to 0/1 integers with no data dictionary**: `temp`,
`nasal_discharge`, `diarrhea`, `difficult_breathing`, `age`, `eye_discharge`,
`oral_nasal_lesion`, `animal`, `sex`, `result` are all binary columns. For the 6 clinical
symptom columns (`temp`, `nasal_discharge`, `diarrhea`, `difficult_breathing`,
`eye_discharge`, `oral_nasal_lesion`) and the `result` target, **0/1 = absent/present is the
only sane reading** and it checks out empirically — every one of them shows a strong, clean
positive correlation with `result` (e.g. `oral_nasal_lesion` present → 83% PPR-positive vs.
17% when absent; `nasal_discharge` present → 85% vs. 15%), consistent with real PPR clinical
presentation (fever, nasal/eye discharge, oral lesions, diarrhea, respiratory distress).

**`animal`, `sex`, and `age` were dropped from the model entirely.** Their 0/1 encoding is
never documented anywhere on the dataset page, in a companion notebook, or in the file
itself — there's no way to confirm which value means "sheep" vs. "goat" for `animal`
(similarly for `sex`, and `age`, which the description calls a continuous "Age" field despite
being binarized here to 0/1). Guessing an encoding (e.g. assuming alphabetical
`LabelEncoder` defaults) would mean silently mislabeling real data — not acceptable for a
diagnosis tool. Because of this, **the model is trained on the full goat+sheep combined file,
not a "sheep-only" subset** — PPR is the same disease in both (same virus, same family,
which is exactly why this study grouped them), so this is a reasonable, disclosed
cross-species choice, not a silent one. It's applied to sheep in the UI because Sheep is the
species this project needed a real model for; the model itself doesn't distinguish species.

## Scope

**Single disease only: PPR (Peste des Petits Ruminants), binary positive/negative.** This is
not a replacement for the cow model's 5-disease coverage — it's a real, narrow, trained
screen for one specific (genuinely serious — PPR is OIE/WHO-notifiable) disease. A negative
result means "not PPR," not "healthy" — the UI discloses this.

## License

**Unknown** — the dataset page lists no license. Same "not verified" honesty bar as
`cattle-images/SOURCE.md`; check with the dataset owner before any redistribution beyond
this project's own local training use.

## Redownload

```python
import kagglehub
path = kagglehub.dataset_download("devothanyambo/ppr-disease-data-from-goats-and-sheep")
```

Single file: `PPR-Goats-Sheep.csv`. Copy it into this directory as-is — the training script
reads it directly, no manual preprocessing needed (the file already arrives pre-encoded).
