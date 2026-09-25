# Spec: Add Mastitis as a 4th image-diagnosable class for Cow

**Milestone**: follow-up to M9 (cattle image classifier)
**Status**: done

> **Real outcome, materially different from the plan below — read this before the rest.**
> The Roboflow dataset described below turned out to have serious, previously-undetected data
> quality problems: manual review of all 319 initially-matched images found the source
> dataset's "online sources" component includes scraped stock photography (iStock/Shutterstock
> watermarks visible on several images) and at least 3 images that aren't cattle at all (human
> hand close-ups, one a video screen-grab). 12 of 48 unique photos in the cleaner-looking
> `Mastitis-N` naming group were excluded for exactly this reason; the messier `Picture-N`/
> `*-400x284` group (~168 images) wasn't used at all. **Final dataset: 47 images, not the
> originally-scoped ~300+** — see `data/cattle-images/SOURCE.md` for the full curation
> writeup, including the residual risk explicitly accepted (some of the 47 "clean" images may
> still be scraped and just not show a visible watermark in that crop). With only 47 images
> (~27x smaller than the other 3 classes), an unweighted training pass completely failed to
> learn the class (Mastitis F1 = 0.0); class-weighted loss (same fix already used in
> `species_classifier_train.py` for a smaller imbalance) got it to a usable but real
> trade-off: 100% recall, ~41% precision, and a 2-4 point F1 cost to each of the other 3
> classes. All of this was surfaced to and decided by the user at each step, not assumed.

## Actor + goal

A farmer/vet uploads a cow photo for image-based diagnosis. Today `image_model.py` only
recognizes 3 classes (`Healthy`, `Lumpy Skin Disease`, `Foot and Mouth Disease`) — Mastitis and
Bovine Respiratory Disease were disclosed gaps (`docs/DISCLAIMER.md`) because no image dataset
existed for either. This closes the Mastitis gap specifically: a cow photo showing a
mastitis-affected udder should come back `{"diagnosis": "Mastitis", ...}` instead of being
forced into one of the 3 existing classes or landing in `uncertain`.

BRD stays out of scope — a real search (this session, prior turn) found no usable public BRD
image dataset; nothing to train on.

## Data source

[cow-and-mastitis-detection](https://universe.roboflow.com/kirubel-yemane/cow-and-mastitis-detection)
(Roboflow Universe, `kirubel-yemane`), **CC BY 4.0**, 2,647 images, 7 object-detection classes:
`Cow_drinking_water`, `Cow_Feeding`, `Cow_lying`, `Cow_standing`, `Healthy_udder`,
`Lumpy_infected_cow`, `Mastitis_infected_udder`.

**Only `Mastitis_infected_udder` is used from this dataset.** Not `Healthy_udder` (the existing
`Healthy` class already has 1,291 well-established photos from a different source — mixing in
a second source for a class that isn't the gap being closed adds domain-shift risk for no
benefit) and not the behavior/`Lumpy_infected_cow` classes (out of scope for this change; see
"Not in scope"). Requires a Roboflow account + API key to export (no anonymous/keyless
download exists for this dataset) — the user is creating the account and providing
`ROBOFLOW_API_KEY` via `ml-service/.env` (gitignored), never pasted in chat.

**Format conversion needed**: this dataset is object-detection (bounding boxes), but every
image model in this project is whole-image classification (one label per photo, folder-per-
class), same as `cattle-images/`, `cat-images/`, `dog-images/`, `goat-images/`. Conversion
rule: an image whose annotations include at least one `Mastitis_infected_udder` box is copied
whole (not cropped) into a new `data/cattle-images/mastitis/` folder with the `Mastitis`
label — same "whole photo, not the annotated region" convention the other classes already use.
Images whose only annotations are non-mastitis classes are dropped (not relevant to this
change).

## Boundaries & failure states

- If the exported dataset has 0 images actually annotated `Mastitis_infected_udder` (possible
  if the annotation format/class name differs from what's documented on the listing page),
  stop and report — don't train on 0 real examples of the class being added.
- If class balance ends up extremely skewed (e.g. Mastitis has an order of magnitude fewer
  images than the existing 3 classes), train anyway but disclose the real per-class F1 rather
  than assume it'll be fine — same "measured, not guessed" standard as every other model in
  this repo.
- Corrupt/unreadable images in the new folder: skipped with a warning, same as
  `image_model_train.py`'s existing `_extract_features` behavior — not a reason to fail the
  whole run.

## Examples

**Happy path**: a real photo showing visible udder swelling/inflammation consistent with
mastitis, Cow selected → `{"diagnosis": "Mastitis", "confidence": 0.7x, "explanation": "...",
"recommended_action": "consult_vet" or "escalate_to_vet" per REPORTABLE_DISEASES, ...}`.
Precautions/next-steps/RAG explanation already work for this — `app/rag/retrieval.py` already
maps `"Mastitis": "mastitis"` and `data/veterinary-reference/mastitis.md` already exists
(the symptom model has diagnosed Mastitis since M1), so no changes needed outside the image
classifier itself.

**Regression check**: existing Healthy/Lumpy Skin Disease/Foot and Mouth Disease photos (from
the original 3-class dataset) must still classify correctly after retrain — a 4th class
shouldn't silently degrade the 3 that already work. Compare per-class F1 before/after, not
just overall accuracy.

## Not in scope

- Bovine Respiratory Disease image coverage — no usable dataset found (see prior research this
  session); still a disclosed gap.
- Reusing this dataset's `Lumpy_infected_cow` images to bolster the existing Lumpy Skin
  Disease class, or its behavior classes (`Cow_drinking_water`/`Feeding`/`lying`/`standing`)
  for anything — out of scope for "add Mastitis," a separate decision if ever pursued.
- Cropping to the annotated udder region instead of using the whole photo — would be a bigger
  behavioral change (users don't crop their uploads to the udder today) and a bigger departure
  from this dataset's raw form than this change needs.
- Any change to the symptom-based Cow model — it already has Mastitis; this is image-only.

## Acceptance criteria (must be checkable)

- [x] `ROBOFLOW_API_KEY` present in `ml-service/.env` (not committed, not pasted in chat).
- [x] `roboflow` added to `ml-service/requirements.txt`.
- [x] Dataset exported (Pascal VOC), converted per the rule above into
      `data/cattle-images/mastitis/` — **with a manual curation pass beyond the automated
      conversion**, not just a straight script run (see the outcome note above and
      `SOURCE.md`). `SOURCE.md` documents the second source, the license caveat, and the
      exclusions in full.
- [x] `app/models/image_model.py`'s `DISEASES` becomes
      `["Healthy", "Lumpy Skin Disease", "Foot and Mouth Disease", "Mastitis"]` (appended, not
      reordered).
- [x] `training/image_model_train.py`'s `FOLDER_TO_DISEASE` gets `"mastitis": "Mastitis"`, plus
      class-weighted loss (not originally planned — added after an unweighted first pass
      completely failed to learn the class).
- [x] Retrained `image_model.pt`, `models/REGISTRY.md` updated with real per-class F1
      (including the 3 pre-existing classes, showing the real 2-4 point regression) and the
      new Mastitis F1 — not assumed, measured (and re-measured after the class-weighting fix).
- [x] `docs/DISCLAIMER.md` updated to 4 of 5 (BRD still the disclosed gap), plus a new
      paragraph on Mastitis's thinner data and its recall/precision trade-off specifically.
- [x] `ml-service/tests/test_agent_graph.py`'s per-class image test extended with a Mastitis
      case (real end-to-end round-trip, plus a non-escalation check since Mastitis correctly
      isn't in `REPORTABLE_DISEASES`).
- [x] Full ml-service suite still green (99/99).
- [x] Live end-to-end check against the running stack (all 4 classes, via the actual backend
      endpoint the frontend calls, not just ml-service directly) — Healthy/Lumpy/FMD/Mastitis
      all correctly diagnosed on real held-out photos.

## Agent mirror-back

**Intent**: close the one image-diagnosis gap that has real, usable, licensed data (found via
this session's dataset survey), without touching the 3 classes that already work and without
scope-creeping into the dataset's unrelated classes (behavior states, Lumpy reinforcement).

**Assumptions flagged**:
1. Whole-image labeling (not cropping to the bounding box) — matches this project's existing
   convention across all 4 other species image models, and how users actually submit photos
   (whole animal/area, not a pre-cropped detail shot).
2. Not merging this dataset's `Healthy_udder` images into the existing `Healthy` folder — the
   existing class already has a solid, single-source dataset; adding a second source only for
   the class that needs it (Mastitis) is the smaller, more conservative change.
3. Retraining the full 4-class head from scratch (not incrementally fine-tuning on just the
   new class) — same "one artifact, one training run" pattern every other retrain in this
   project (Dog v1→v2, Cat, Goat) has used; there's no existing precedent here for incremental
   class-addition and introducing one would be a bigger, less-tested change than just retraining.
