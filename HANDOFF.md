# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-24) — continuation of `feat/m16-goat-species-and-dog-v2`

You reported two things after the M16/Dog-v2 PR: (1) uploading a wrong-species or unrelated
image still "gives some output" instead of being caught, and (2) wanted a button to re-analyze
with a different species. Both addressed.

- **The species-mismatch detector was genuinely broken, not just imperfect** — reproduced
  before touching any code: 3 of 8 real dog photos submitted as Cow came back a confident
  **"Foot and Mouth Disease"** with `escalate_to_vet`. This was a real regression from the
  same session's Dog dataset swap (M16), previously only *disclosed* in docs, not fixed. The
  "is this an animal at all" gate was never the problem — every non-animal fixture still
  correctly rejected.
- **Root cause and fix**: the old detector repurposed an unrelated, off-the-shelf ImageNet-1k
  classifier's class probabilities as a proxy for species. Replaced with a **real classifier
  trained on this project's own cat/cow/dog/goat photos**
  (`ml-service/app/models/species_classifier.py` + `training/species_classifier_train.py`) —
  5,894 photos already downloaded for the disease classifiers, no new dataset. Deliberately
  includes **both** Dog photo sets (v2 skin close-ups and the retained v1 whole-body set) as
  training data, so the exact close-ups that broke the old approach are now real ground truth.
- **Caught a second real bug during calibration, before shipping anything**: the first
  (unweighted-loss) trained model was 84.9% accurate but biased toward COW (3,244 training
  photos vs. Dog's 724, ~4.5x imbalance) — real Dog photos scored *higher* on COW than DOG,
  and any threshold sensitive enough to catch the reported bug well was false-rejecting ~15%
  of genuine Dog submissions. Fixed with inverse-frequency class-weighted loss (no data
  discarded) — final model: **89.2% accuracy, 0.857 macro F1**.
- **Measured result** at the chosen threshold (2.0): dog-as-cow (the reported pair) now
  catches 92.4% (was ~30% before this fix), goat-as-cow 86.5%, everything else 81-98%.
  Same-species false-reject is 4.3% overall (Goat highest at 8.1% — the new weakest spot,
  disclosed, not chased further). Re-verified directly against the *exact* photos from the
  original bug report through the real running backend + ml-service — all now correctly
  return `species_mismatch` instead of a disease name.
- **New feature**: a "🔁 Analyze with a different species" button appears after any
  image-based result — keeps the uploaded photo(s), clears the result, focuses the species
  dropdown. Lets someone correct a wrong species guess (whether the detector caught it or,
  since it's not perfect, didn't) without re-attaching anything. Only shown when a photo was
  actually submitted; `SpeciesField.jsx` now forwards a ref so focus can move there
  programmatically, matching the existing focus-management pattern for results.
- Docs: new [docs/specs/species-classifier.md](docs/specs/species-classifier.md);
  `docs/specs/species-mismatch-and-actionable-results.md` annotated (not rewritten) as
  superseded-mechanism; `docs/DECISIONS.md`, `docs/DISCLAIMER.md`, `docs/API_CONTRACTS.md`
  updated with the real final numbers.
- **Validated**: ml-service 95 passed / 1 skipped, backend unaffected and re-confirmed green,
  frontend lint clean + 29/29 tests + production build, plus live end-to-end verification
  (real backend + ml-service + browser) — including catching and fixing a stale-process port
  collision along the way (same class of issue as the M16 session; check `netstat` before
  trusting a "green" verification if default ports might be occupied by another session).

### What shipped

- **Nothing has been committed yet this continuation** — the M16 work was already committed
  and PR'd (#42) in the prior part of this session; this session's fix (species classifier +
  retry button) is uncommitted on top of that on the same branch. Ask before committing —
  probably as a second commit on the same PR, since it's fixing a bug reported against work
  that PR already contains, but confirm with the user rather than assuming.
- The species classifier's feature-extraction step is slow (~3-4 min for 5,894 images on
  CPU) — if retraining it again, cache pooled features to a `.npz` file first (a scratch
  script did this this session) rather than re-extracting for every calibration iteration.
- Goat-as-cow (86.5% caught) and cat-as-dog/goat-as-dog (~81-83%) are the remaining weakest
  mismatch pairs — real, disclosed, not chased down further. If revisited, more Goat/Dog
  training photos (not just reweighting) would be the next lever.
- Could not literally drive the file picker in the built-in browser tool to visually verify
  the new retry-species button end-to-end (same limitation prior sessions noted) — covered
  instead by two new Vitest tests using `user.upload()` simulation, plus curl-based
  verification of the underlying species-classifier fix.

## Blockers

- None new.
