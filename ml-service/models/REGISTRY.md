# Model Registry

Trained model artifacts are gitignored (`*.pkl`/`*.pt`/`*.onnx`) — track versions here instead.

| File | Disease | Trained on | Metric | Date |
|---|---|---|---|---|
| `symptom_model.pkl` | all (multiclass) | synthetic-symptom-dataset (750 rows) | acc=0.888, f1_macro=0.888 | 2026-09-16 |
| ~~`image_model.pt`~~ | ~~Healthy / Lumpy Skin Disease / Foot and Mouth Disease (not Mastitis/BRD)~~ **superseded, see the 2026-09-24 row below** | cattle-images (3244 images) | acc=0.861, f1_macro=0.857 | 2026-09-20 |
| `cat_image_model.pt` | Flea Allergy / Healthy / Ringworm / Scabies (replaces M13's URI/FIV research list — no image data for those) | cat-images (999 images) | acc=0.830, f1_macro=0.829 | 2026-09-20 |
| ~~`dog_image_model.pt`~~ | ~~Canine Distemper / Canine Parvovirus / Kennel Cough / Mange (no Healthy class)~~ **superseded, see the v2 row below — the v1 artifact no longer exists on disk** | dog-images v1, 285 images (moved to `data/dog-images-v1-superseded/`) | acc=0.526, f1_macro=0.489 | 2026-09-20 |
| `sheep_symptom_model.pkl` | PPR (Peste des Petits Ruminants) — binary, goat+sheep combined (see SOURCE.md — species column undecodable) | sheep-symptoms/PPR-Goats-Sheep.csv (21199 rows) | acc=0.805, f1_macro=0.788 | 2026-09-22 |
| `goat_image_model.pt` | Healthy / Unhealthy (binary — no disease-specific goat image data exists, see SOURCE.md) | goat-images (927 images) | acc=0.801, f1_macro=0.800 | 2026-09-23 |
| `dog_image_model.pt` (v2) | Bacterial Dermatosis / Fungal Infection / Healthy / Hypersensitivity-Allergic Dermatosis (v2 dataset, replaces the v1 systemic-disease list — see SOURCE.md) | dog-images (439 images) | acc=0.705, f1_macro=0.683 | 2026-09-23 |
| `species_classifier.pt` | species identity (CAT/COW/DOG/GOAT), not a disease — replaces the ImageNet-heuristic species-mismatch check; class-weighted loss (see SOURCE — COW outnumbers DOG ~4.5x unweighted) | cat/cattle/dog(+v1)/goat-images combined (5894 images) | acc=0.892, f1_macro=0.857 | 2026-09-24 |
| `image_model.pt` | Healthy / Lumpy Skin Disease / Foot and Mouth Disease / Mastitis (not BRD) — class-weighted loss (Mastitis has only 47 curated images against 746-1291 for the other 3, ~27x; an unweighted first pass scored Mastitis F1=0.0, completely unlearned — see SOURCE.md/cow-mastitis-image-classifier.md). Weighted result: Mastitis recall 100% (9/9 val photos caught) but precision ~41% (13 Lumpy/FMD photos misclassified as Mastitis) — real trade-off, not tuned away; the other 3 classes each dropped 2-4 F1 points from the pre-Mastitis baseline (Healthy 0.852→0.829, Lumpy 0.892→0.872, FMD 0.810→0.776) as the real, disclosed cost | cattle-images (3291 images, incl. 47 Mastitis) | acc=0.825, f1_macro=0.764 | 2026-09-24 |
