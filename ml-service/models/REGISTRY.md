# Model Registry

Trained model artifacts are gitignored (`*.pkl`/`*.pt`/`*.onnx`) — track versions here instead.

| File | Disease | Trained on | Metric | Date |
|---|---|---|---|---|
| `symptom_model.pkl` | all (multiclass) | synthetic-symptom-dataset (750 rows) | acc=0.888, f1_macro=0.888 | 2026-09-16 |
| `image_model.pt` | Healthy / Lumpy Skin Disease / Foot and Mouth Disease (not Mastitis/BRD) | cattle-images (3244 images) | acc=0.861, f1_macro=0.857 | 2026-09-20 |
| `cat_image_model.pt` | Flea Allergy / Healthy / Ringworm / Scabies (replaces M13's URI/FIV research list — no image data for those) | cat-images (999 images) | acc=0.830, f1_macro=0.829 | 2026-09-20 |
| `dog_image_model.pt` | Canine Distemper / Canine Parvovirus / Kennel Cough / Mange (no Healthy class — see SOURCE.md) | dog-images (285 images) | acc=0.526, f1_macro=0.489 | 2026-09-20 |
| `sheep_symptom_model.pkl` | PPR (Peste des Petits Ruminants) — binary, goat+sheep combined (see SOURCE.md — species column undecodable) | sheep-symptoms/PPR-Goats-Sheep.csv (21199 rows) | acc=0.805, f1_macro=0.788 | 2026-09-22 |
