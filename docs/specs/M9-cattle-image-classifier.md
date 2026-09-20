# Spec: Real cattle image classifier

**Milestone**: M9
**Status**: done — dataset downloaded (no Kaggle token needed for this public dataset, unlike
the "Blocker" section below assumed), model trained and wired in. See STATE.md for the full
session detail.

## Actor + goal

A farmer/vet uploads a cattle photo and `predict_image_node` (currently a deterministic
byte-hash placeholder, M8 phase 1) returns a real disease prediction from the image content,
in the same `{diagnosis, confidence, top_features}` shape `predict_symptoms_node` already
produces, so `explain`/`recommend` don't need to change.

## Blocker (read first, resolved 2026-09-20)

**Resolved**: `kagglehub.dataset_download(...)` downloaded this dataset anonymously — no
Kaggle account/API token was actually required for this public dataset, contrary to what the
section below assumed. See `ml-service/data/cattle-images/SOURCE.md`.



Training needs real images. The candidate dataset —
[Cattle Diseases Datasets (Kaggle, devang03mgr)](https://www.kaggle.com/datasets/devang03mgr/cattle-diseases-datasets),
3,244 images across Healthy/Lumpy Skin Disease/Foot-and-Mouth Disease — requires a Kaggle
account and API token to download, which this environment doesn't have (no `~/.kaggle/`
config, no `KAGGLE_USERNAME`/`KAGGLE_KEY` env vars). This is the same blocker M1's spec hit
for the symptom dataset (see `docs/specs/M1-baseline-symptom-model.md`'s deviation #1) — that
one was resolved by falling back to a synthetic dataset instead, which **is not a viable
fallback here**: a procedurally-generated "image" carries none of the actual visual signal a
CNN needs to learn, so a synthetic image dataset wouldn't produce a classifier that
means anything, unlike M1's synthetic *tabular* data (which encoded a real, documented
statistical relationship between symptoms and disease).

**What unblocks this**: either (a) download the dataset from the link above and tell me the
local folder path, or (b) put a Kaggle API token where the `kaggle` CLI expects it
(`~/.kaggle/kaggle.json`, or `KAGGLE_USERNAME`/`KAGGLE_KEY` env vars) — not pasted in chat —
and I'll run the download myself once it's in place.

## Boundaries & failure states

- Scope is the 3 classes the candidate dataset actually has: `Healthy`, `Lumpy Skin
  Disease`, `Foot and Mouth Disease`. The symptom model's other 2 classes (`Mastitis`,
  `Bovine Respiratory Disease`) are **not** covered by image prediction after this
  milestone — document this explicitly in `docs/API_CONTRACTS.md`, don't silently imply
  parity with the symptom model's 5-class coverage.
- Approach: transfer learning on a small pretrained torchvision backbone (e.g.
  MobileNetV2), fine-tuning only the classifier head — appropriate for ~3k images and
  CPU-feasible training time, versus training a CNN from scratch (would need far more data
  and compute than this "learning project" has). New dependencies: `torch`, `torchvision`
  (CPU wheels — no GPU assumed).
- Same artifact convention as M1: the trained weights file is gitignored, an entry goes in
  `ml-service/models/REGISTRY.md` (file, classes, dataset, metric, date) instead.
- If the model's top-class confidence is below a documented threshold (mirror M1's `0.4`
  unless evaluation suggests otherwise), return `"uncertain"` rather than a low-confidence
  label presented as reliable — same pattern as the symptom model.
- `predict_image_node` must not raise on a corrupt/unreadable image file — degrade to
  `"uncertain"`, matching the existing "never blocks a diagnosis" pattern already used for
  network/decode failures in the M8 placeholder.

## Examples

**Input**: JPEG/PNG bytes of a cow with visible skin nodules.

**Expected output shape** (same as `predict_symptoms_node`):
```json
{
  "diagnosis": "Lumpy Skin Disease",
  "confidence": 0.87,
  "top_features": []
}
```
`top_features` stays `[]` for the image path — per-pixel/region attribution (e.g. Grad-CAM)
would be the image equivalent of SHAP, but is a stretch goal, not required for this
milestone (mirrors M1's own "hyperparameter tuning is a stretch goal" scoping call).

**Edge case — corrupt/unreadable image**: `diagnosis: "uncertain"`, `confidence` below
threshold, same as the existing `_fetch_image_bytes` failure path in M8.

## Not in scope

- Mastitis/Bovine Respiratory Disease image recognition (dataset doesn't cover them —
  future work if a dataset covering them turns up).
- Any other species (M11-M14 — those are separate milestones with their own datasets).
- Grad-CAM/attribution visualization (stretch goal, see above).
- Mobile/edge inference optimization (quantization, ONNX export, etc.).

## Acceptance criteria

- [x] Dataset downloaded and documented in a `SOURCE.md` (source URL, license, class
      counts) under `ml-service/data/`, same convention as the existing `SOURCE.md` files.
- [x] Training script `ml-service/training/image_model_train.py`, mirroring
      `symptom_model_train.py`'s structure (documented, reproducible, writes to
      `ml-service/models/REGISTRY.md`).
- [x] Real evaluation metrics recorded (accuracy/F1 per class, confusion matrix) — not just
      "it works." 86.1% accuracy / 0.857 macro F1 on a held-out validation split.
- [x] `predict_image_node` (`ml-service/app/agent/graph.py`) uses the trained model in place
      of `_placeholder_diagnosis_from_bytes`.
- [x] The `image_placeholder` branch in `explain_node` is removed — image-based
      explanations go through the same LLM/RAG path as symptom-based ones now that there's a
      real model behind them.
- [x] `docs/API_CONTRACTS.md` and `docs/DISCLAIMER.md` updated: image prediction covers 3
      classes, not the symptom model's full 5.
- [ ] Tests updated: the M8 placeholder-specific tests in `test_agent_graph.py`/
      `test_diagnose_endpoint.py` (determinism-of-a-hash, "placeholder" wording assertions)
      replaced with real-model tests (a confident prediction per class, the uncertain/corrupt
      cases, escalation still fires for LSD/FMD).
- [ ] Full build/test suite green, plus manual end-to-end verification with a real photo
      per class.

## Agent mirror-back

**Intent**: swap the M8 placeholder for a real, if modest, trained image classifier —
transfer learning rather than training from scratch, scoped to exactly the 3 classes real
data exists for, with the same honesty-about-limitations posture M1 used for its synthetic
symptom data (M1 disclosed "synthetic, not real"; this milestone discloses "3 of 5 disease
classes, not full parity").

**Inputs/outputs**: unchanged from M8's `predict_image_node` interface — image bytes in,
`{diagnosis, confidence, top_features}` out.

**Assumptions flagged before coding**:
1. Torch/torchvision added as new `ml-service` dependencies — heavier than anything else in
   `requirements.txt` so far; worth flagging since this project has otherwise stayed
   light (XGBoost, not a deep-learning framework, for M1).
2. Blocked on real data, per above — nothing past "write the spec" happens until the
   dataset is actually available locally.
