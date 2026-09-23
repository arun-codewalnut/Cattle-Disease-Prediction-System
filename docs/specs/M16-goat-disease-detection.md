# Spec: Goat disease detection

**Milestone**: M16
**Status**: done

## Actor + goal

A farmer/vet can select "Goat" in the species selector and get a real diagnosis from a photo
— the user asked directly for the goat dataset to be downloaded and integrated, unlike
Cat/Dog/Sheep, which were added first and got a real model only as later follow-up work.

## Why Goat gets a real model from day one, but a binary one

Unlike M13 (Cat) and M14 (Dog), which deliberately blocked diagnosis entirely at first
because no dataset existed, a real search this session found
[Healthy and Unhealthy Goat Images](https://www.kaggle.com/datasets/kartikeybartwal/dataset)
(Apache 2.0, downloadable anonymously via `kagglehub`, same pattern as every other dataset in
this project) — so there was no "block, don't approximate" decision to make.

**But the dataset is binary, not disease-specific.** Queries tried against Kaggle's public
search API this session — "goat disease", "goat skin disease", "goat pox", "goat images" —
turned up nothing with named disease classes. This is a real, structural difference from
Cat's and Dog's models: **the goat model can say a photo looks off, but never names what's
wrong.** `DISEASES = ["Healthy", "Unhealthy"]` in `app/models/goat_image_model.py` reflects
that honestly rather than inventing plausible-sounding disease labels the data doesn't
support.

No goat symptom model exists either — the closest candidate, the PPR dataset that trains
Sheep's symptom model, combines goat and sheep rows with an undecodable species column (see
`data/sheep-symptoms/SOURCE.md`), so there's no way to isolate a goat-only symptom signal.
Goat is **image-only**, like Cat and Dog, via `IMAGE_ONLY_SUPPORTED_SPECIES` on both the
backend and frontend.

## Examples

**Happy path**: `POST /api/diagnoses/image` with `species=GOAT` and a photo of a goat with
visible lesions → `{"species": "GOAT", "diagnosis": "Unhealthy", "confidence": 0.81,
"recommendedAction": "consult_vet", "precautions": [...], "nextSteps": [...]}`.

**Edge case — symptom endpoint**: `POST /api/diagnoses` with `species=GOAT` →
`400 {"code": "DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES", ...}` — same shape Cat/Dog already
return for symptom submissions, no new error code needed.

**Edge case — species mismatch**: a cat or dog photo submitted with Goat selected →
`diagnosis: "species_mismatch"`, no confidence, `recommended_action: "retry_upload"` — same
mechanism Cow/Sheep/Cat/Dog already use (see "Species-mismatch detection" below).

## Species-mismatch detection: a real measured limitation, not assumed to just work

ImageNet-1k (the pretrained classifier `species_gate.py` already uses for the animal gate and
species-mismatch check) has **no dedicated "goat" class** — verified directly against
`MobileNet_V2_Weights.DEFAULT.meta['categories']`, not assumed. The closest available proxy
is **"ibex"** (index 350, a wild goat species), added to the existing `RUMINANT` group
alongside ox/water buffalo/bison/ram/bighorn (indices 345-349) — Goat shares this group with
Cow and Sheep, the same "no dedicated model, group with what's biologically closest" pattern
Sheep already uses for its own image path.

**Measured before shipping** (40-photo samples from this project's own real goat/cat/dog
photos):

| check | rate |
|---|---|
| goat-as-GOAT false reject | 5% (2/40) |
| cat-as-GOAT caught | 90% (18/20) |
| dog-as-GOAT caught | 30% (6/20) |
| goat-as-COW (should mostly pass, same group) | 5% (2/40) |
| cow-as-COW (regression check — adding ibex must not change this) | unaffected |

The false-reject rate on real goat photos is comparable to other species (~5%), so the group
addition is safe to ship. **Dog-as-goat detection is weaker than dog-as-cow's documented 84%**
— goat's signal leans entirely on ibex, a much narrower proxy than cattle's own dedicated
classes, so the model's opinion about "ruminant" is noisier for goat photos specifically. This
is the same kind of directional weakness already documented for the existing detector (see
`docs/DECISIONS.md`'s "livestock under Cat/Dog not caught" note) — disclosed here rather than
assumed away.

## A second, unplanned finding: Dog's dataset swap weakened dog-as-cow detection

Swapping Dog's disease dataset to skin-lesion close-ups (see the Dog follow-up in
`docs/specs/M14-dog-disease-detection.md`) had a side effect nothing in this spec originally
asked for: **the species-mismatch detector's ability to catch a dog photo submitted as Cow
dropped from ~80% (whole-body v1 photos) to ~30% (v2 skin close-ups)**, measured on 40-photo
samples of each. Close-up lesion shots don't show the face/ears/snout features the
ImageNet-based detector actually keys on for "this is a dog." Logged as a `docs/DECISIONS.md`
entry rather than silently absorbed — the test suite's fixture for this check now
deliberately reads from the retained `data/dog-images-v1-superseded/` folder instead, so the
detector's real capability stays covered by a stable, representative fixture independent of
whichever dataset currently trains the disease classifier.

## Boundaries & failure states

- `species: "GOAT"` is a valid value on both diagnosis endpoints.
- The symptom endpoint (`POST /api/diagnoses`) rejects `GOAT` with
  `DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES` — no symptom model exists.
- The image endpoint accepts `GOAT` and returns `Healthy`, `Unhealthy`, `uncertain`,
  `invalid_image`, or `species_mismatch` — never a named disease, since none exists in the
  model.
- Goat's `Unhealthy` result gets real precautions/next-steps text
  (`data/veterinary-reference/unhealthy-goat.md`) — generic ("isolate the animal, consult a
  vet"), since there's no specific disease to give disease-specific guidance for.

## Not in scope

- A disease-specific goat model — blocked on data, same as Buffalo was before it was removed.
  If a real goat-disease dataset turns up later, this is a natural follow-up.
- A goat symptom model — the only candidate data (PPR) can't be split by species.
- Any change to Cow/Sheep/Cat behavior.
- Fixing the weakened dog-as-cow mismatch detection identified above — documented as a real,
  accepted tradeoff for this session (the accuracy gain from the new Dog dataset was judged
  worth it), not silently ignored, but not actively worked around either.

## Acceptance criteria

- [x] `GOAT` added to the backend `Species` enum and frontend `SPECIES_OPTIONS`.
- [x] Backend rejects symptom diagnosis for `GOAT` with `DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`
      — covered by a test.
- [x] Backend accepts image diagnosis for `GOAT` and forwards species to ml-service —
      covered by a test.
- [x] `app/models/goat_image_model.py` + `training/goat_image_model_train.py` follow the
      same MobileNetV2-transfer-learning pattern as Cat/Dog/Cow.
- [x] Real trained model: 80.1% validation accuracy, 0.800 macro F1 across Healthy/Unhealthy
      (927 images, `kartikeybartwal/dataset`, Apache 2.0).
- [x] `species_gate.py`'s `RUMINANT` group and animal gate both cover Goat, measured (not
      assumed) before shipping — see the table above.
- [x] `docs/DISCLAIMER.md` updated: Goat's binary-only limitation stated plainly, and the
      dog-as-cow detection regression logged.
- [x] `docs/API_CONTRACTS.md` updated: `GOAT` as a valid species value, image-only support.
- [x] `docs/DECISIONS.md` updated: the ibex-proxy choice, the binary-model choice, and the
      unplanned dog-mismatch-detection regression, each with real measurements.
- [x] Full build/test suite green across all three services — ml-service 94/1 (skipped),
      backend 32/32, frontend lint + 27/27 + build — plus live end-to-end verification
      against the real running stack (see HANDOFF.md/STATE.md for the verification note).

## Agent mirror-back

**Intent**: download and integrate a goat dataset per the user's direct request, and — since
the user asked to cover "all species" datasets that exist — also replace Dog's weak, no-
Healthy-class model with a better one, since real candidate data was found for it too. Two
scope questions were asked and answered before implementation (`AskUserQuestion`): Goat
becomes a full new species (not folded into Sheep), and the "other species" work is
specifically the weak Dog model (not a new species classifier to replace the ImageNet gate).

**Assumptions/findings flagged before and during coding**:
1. Goat's dataset is binary, not disease-specific — the model's real capability is narrower
   than Cat/Dog's, and the spec/disclaimer say so plainly rather than implying disease-level
   specificity that doesn't exist.
2. ImageNet has no dedicated goat class; "ibex" is used as the closest proxy, verified
   directly against the model's own category list rather than guessed.
3. The species-mismatch detector's dog-as-cow accuracy measurably dropped as an unplanned
   side effect of the Dog dataset swap (not something this spec set out to change) — logged
   as a real, accepted tradeoff rather than silently absorbed or worked around under time
   pressure.
