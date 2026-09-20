# Model Registry

Trained model artifacts are gitignored (`*.pkl`/`*.pt`/`*.onnx`) — track versions here instead.

| File | Disease | Trained on | Metric | Date |
|---|---|---|---|---|
| `symptom_model.pkl` | all (multiclass) | synthetic-symptom-dataset (750 rows) | acc=0.888, f1_macro=0.888 | 2026-09-16 |
| `image_model.pt` | Healthy / Lumpy Skin Disease / Foot and Mouth Disease (not Mastitis/BRD) | cattle-images (3244 images) | acc=0.861, f1_macro=0.857 | 2026-09-20 |
