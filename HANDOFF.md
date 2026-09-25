# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-24) — Cow Mastitis added as a 4th image class

Followed on from a broader user ask ("train on all diseases per species so diagnosis gives
related output") — a dataset survey that same session found real public data for exactly one
gap: Cow Mastitis (image). User said go ahead. See
`docs/specs/cow-mastitis-image-classifier.md` for the full story; the short version is that
almost nothing about the original plan survived contact with the actual data.

- **The Roboflow source dataset's CC BY 4.0 label was misleading.** Downloaded
  `cow-and-mastitis-detection` (user provided their own free API key), converted the
  object-detection export to this project's whole-image convention — 319 images initially
  matched the Mastitis class. **Manually reviewed every one of them** (not a sample) rather
  than trusting the label, and found: visible iStock/Shutterstock watermarks on several
  images (scraped stock photography, not original work), at least 3 images that aren't cattle
  at all (human hand close-ups, one a literal video screen-grab with a captions watermark),
  and the `Mastitis-N` filenames turned out to be 140 files but only **48 unique photos** (3
  rotated duplicate crops each, which would have leaked across train/val splits undetected).
  **Stopped and asked the user at two separate decision points** rather than push through
  silently: first when the scale of contamination became clear, then again after finding it
  ran through the "clean-looking" bucket too, not just the messy one. User chose to accept the
  residual risk and use the 47 confirmed-unwatermarked photos.
- **47 images (~27x smaller than the other 3 classes) broke plain training** — Mastitis
  scored 0.0 F1, completely unlearned by an unweighted loss. Fixed with class-weighted loss
  (same pattern `species_classifier_train.py` already used for a smaller imbalance): real
  result is 100% recall / ~41% precision on Mastitis, and a 2-4 point F1 cost to each of the
  other 3 classes — a genuine, disclosed trade-off, not tuned away.
- **Validated**: full ml-service suite 99/99, plus all 4 classes (Healthy/Lumpy/FMD/Mastitis)
  verified live through the actual backend endpoint the frontend calls, not just ml-service
  directly.
- Docs carrying the real numbers and the full curation story: `data/cattle-images/SOURCE.md`
  (most detail — read this first if picking this back up), `docs/DISCLAIMER.md`,
  `models/REGISTRY.md`, `docs/specs/cow-mastitis-image-classifier.md`.
- New infra left behind, reusable for a future dataset: `roboflow` SDK in
  `requirements.txt`, `training/fetch_mastitis_data.py` (download+convert script — its
  `ROBOFLOW_API_KEY` is in `ml-service/.env`, gitignored, still there for reuse).

## Next session

- **Four separate, uncommitted changes are sitting on `main` right now** — ask before
  committing, these are logically distinct and probably deserve separate PRs:
  1. Species-mismatch classifier threshold fix + first animal-gate retune +
     `GlobalExceptionHandler`/`DiagnosisControllerTest` fix — see "Full positive/negative
     scenario pass" in `docs/DECISIONS.md`. `backend/src/test/java/.../DiagnosisControllerTest.java`
     is still untracked (part of this one).
  2. Result-card redesign + single-button change (`DiagnosisIntake.jsx`/`DiagnosisResult.jsx`/
     `App.css`).
  3. Per-species animal-gate threshold fix (diagram/chart false-accept bug) — new fixtures in
     `tests/fixtures/non-animal-diagram-*.png`.
  4. This session: Cow Mastitis 4th class — new `data/cattle-images/mastitis/` (47 images,
     gitignored like the rest of `data/`), `training/fetch_mastitis_data.py`, retrained
     `image_model.pt` (gitignored, not committed — whoever picks this up needs to retrain
     locally or the artifact needs sharing some other way).
- **The other Roboflow bucket (~168 images, `Picture-N`/`*-400x284` naming) was never
  reviewed** — deliberately not used this session given how the first bucket turned out, but
  not confirmed bad either. A real "is there more usable Mastitis data in here" question if
  ever revisited — would need the same manual-review treatment before trusting any of it.
- **The Mastitis precision problem (~41%) is a real, live cost** — worth watching if real
  users start hitting false-positive Mastitis calls on Lumpy/FMD photos. More real, clean
  Mastitis data (not more threshold tuning) is the actual fix if this needs revisiting.
- Nothing else changed from earlier open items (Dog's ~13% combined block rate, Goat's
  placeholder-image contamination, the "temp"-not-humanized Sheep explanation wording,
  diagram/chart gate's own disclosed remaining gap) — still real, still not chased further.

## Blockers

- None new.
