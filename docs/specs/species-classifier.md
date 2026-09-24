# Spec: Real species classifier for species-mismatch detection

**Milestone**: follow-up to M15/species-mismatch-and-actionable-results, prompted directly by
the user reporting the check wasn't working
**Status**: done

## Actor + goal

A farmer/vet selects a species and uploads a photo of a *different* animal (by mistake, or an
unrelated photo). The system must refuse to diagnose rather than confidently naming a disease
for the wrong animal — this already existed (`species_gate.looks_like_a_different_species`)
but the user reported, correctly, that it was letting real mismatches through.

## What was actually wrong

Reproduced directly against the running stack before touching any code:

- 3 of 8 real dog photos submitted with `COW` selected came back **"Foot and Mouth Disease"**
  with `escalate_to_vet` — a confidently wrong, escalating diagnosis of a reportable disease,
  from a dog photo.
- 2 of 6 real cat photos submitted with `DOG` selected came back real disease names
  ("Bacterial Dermatosis" 71%, "Fungal Infection" 51%) instead of being caught.
- The "is this even an animal" gate (`is_animal_photo`) was **not** the problem — every
  non-animal fixture was still correctly rejected for all 5 species.

Root cause: the previous `looks_like_a_different_species` repurposed a generic, off-the-shelf
ImageNet-1k classifier's class probabilities (e.g. "ox," one of 118 dog breeds) as a proxy for
"does this look like species X." That proxy was never trained on this project's own photos,
and it measurably collapsed once Dog's disease dataset became skin-lesion close-ups (see the
"M16 follow-up" entry in `docs/DECISIONS.md`): dog-as-cow catch rate dropped from ~80%
(whole-body v1 photos) to ~30% (v2 close-ups), because a close-up doesn't show the
face/ears/snout features the generic ImageNet dog classes actually key on. Disclosing this in
docs, without fixing it, was not enough — the user is right that "documented limitation" and
"fixed" are not the same thing when the failure mode is a confidently wrong, escalating
diagnosis.

## The fix: a real classifier trained on this project's own photos

`app/models/species_classifier.py` + `training/species_classifier_train.py` — same
MobileNetV2-transfer-learning pattern already used throughout this project (`image_model.py`,
`cat_image_model.py`, etc.), fine-tuned on **5,894 real photos already downloaded for the
disease classifiers** (no new dataset needed): `cattle-images` (COW), `cat-images` (CAT),
`dog-images` + `dog-images-v1-superseded` combined (DOG — deliberately both the current
skin-close-up set and the retained whole-body set, so the classifier learns to recognize a dog
from a skin lesion close-up too, not just a whole photo — the exact gap that broke the old
approach), `goat-images` (GOAT).

**First attempt: 84.9% accuracy, 0.781 macro F1** with a plain (unweighted) loss. Per-class
F1: COW 0.911, CAT 0.862, GOAT 0.724, DOG 0.628. This shipped a second real bug (caught before
release, not after): COW's 3,244 training photos against DOG's 724 (~4.5x imbalance) silently
biased the model toward COW — real Dog "healthy" photos scored *higher* on COW than DOG
(e.g. 0.68 vs 0.11), which fed straight into the mismatch check and false-rejected genuine Dog
submissions 15.2% of the time (Goat: 10.8%) — worse for real users than the bug being fixed.

**Fixed with inverse-frequency class-weighted loss** (`nn.CrossEntropyLoss(weight=...)`,
computed from the actual training split's class counts) — no data discarded, same real 5,894
photos. **Final result: 89.2% accuracy, 0.857 macro F1.** Per-class F1: COW 0.943, CAT 0.873,
GOAT 0.841, DOG 0.773 — DOG went from the weakest class by a wide margin to broadly in line
with the others. `SHEEP` has no photos anywhere in this project (same wall its own symptom
model's `SOURCE.md` documents) — mapped onto the `COW` class for this check, same "no data,
use the closest approximation" precedent Sheep's disease routing already set.

## Choosing the decision rule — measured, not guessed

Used the (final, class-weighted) classifier's own held-out validation split (1,179 real
photos it never trained on) to measure, for every (true species, wrongly-selected species)
pair, the ratio of the best *other* class's probability to the wrongly-selected class's own
probability. At the chosen threshold of **2.0**: overall catch rate 91.0%, overall
false-reject 4.3% — already better on both axes than the pre-existing ImageNet-heuristic
system's own baseline (5-7.5% false-reject).

| pair              | caught | | same-species false-reject | rate |
|-------------------|-------:|-|----------------------------|-----:|
| dog as cow         | 92.4% | | CAT (own class)            | 2.5% |
| goat as cow        | 86.5% | | COW (own class)            | 3.5% |
| cat as dog         | 81.5% | | DOG (own class)            | 5.5% |
| goat as dog        | 83.2% | | GOAT (own class)           | 8.1% |
| everything else    | 88-98%| |                            |      |

Both pairs that mattered most — dog-as-cow (the exact pair originally reported broken) and
goat-as-cow (the two most visually similar species in this project's photos) — now catch
above 85%, a large jump from the unweighted model's 57-68% at the same threshold. Goat has the
highest same-species false-reject (8.1%) — the new weakest spot in the system after the fix,
real and disclosed, still far better than any pair was before the fix existed.

## Examples

**Happy path**: a real dog photo (from either the v1 whole-body set or the v2 skin-close-up
set) submitted with `DOG` selected → normal diagnosis, unaffected.

**The bug this fixes**: the same dog photo submitted with `COW` selected → `diagnosis:
"species_mismatch"`, `confidence: 0.0`, `recommended_action: "retry_upload"` — verified
against the exact photos that slipped through before this fix.

**Known weak case, disclosed not hidden**: a goat photo submitted with `COW` selected has a
meaningfully lower (but non-zero) chance of being caught than other mismatched pairs.

## Not in scope

- A dedicated Sheep species classifier — no sheep photos exist anywhere in this project.
- Retraining any *disease* classifier — this only touches which-species detection.
- Confirming a photo shows the *correct individual animal* — still, as always, only "does
  this look like the selected species," never anything about the specific animal.

## Acceptance criteria

- [x] `app/models/species_classifier.py` + `training/species_classifier_train.py`, same
      pattern as the existing per-species disease classifiers.
- [x] Real trained model: 89.2% accuracy, 0.857 macro F1 (class-weighted loss, after an
      unweighted first attempt was measured to bias the model toward COW), `models/species_classifier.pt`.
- [x] `species_gate.looks_like_a_different_species` rewritten to use the new classifier;
      `is_animal_photo` untouched (it was never the broken part).
- [x] Threshold chosen from measured held-out validation data, documented with the real
      trade-off table, not picked by feel.
- [x] Re-verified against the exact real photos that slipped through in the original bug
      report — now correctly flagged as `species_mismatch`.
- [x] `docs/DECISIONS.md`, `docs/DISCLAIMER.md` updated with the real numbers.
- [x] Full test suite green across all three services.

## Agent mirror-back

**Intent**: fix a real, reproduced bug (wrong-species photos producing confident, escalating,
wrong diagnoses) with a real fix (a classifier trained on this project's own data), not a
threshold tweak on the existing broken approach — the investigation showed a threshold tweak
couldn't fix it, since the underlying signal (generic ImageNet dog classes) genuinely doesn't
transfer to the close-up photos this project's own Dog dataset now consists of.

**Assumptions flagged**:
1. Sheep still has no photos of its own — mapped to COW for this check, consistent with how
   Sheep's disease diagnosis already falls back to the cattle model.
2. The goat-as-cow weak spot is a real, disclosed limitation, not something this session
   chased down further — goat and cow genuinely look similar in this project's own photos,
   and no amount of threshold tuning changes that without more/better data.
