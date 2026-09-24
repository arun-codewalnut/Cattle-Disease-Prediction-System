# Spec: Species-mismatch warning, and results that lead with what to do

**Milestone**: stretch (post-M15)
**Status**: agreed — **the detection mechanism this spec designed (ImageNet-1k class-group
ratios) was later replaced by a real trained classifier**, see
[docs/specs/species-classifier.md](species-classifier.md) and `docs/DECISIONS.md`. The
product behavior this spec describes (refuse rather than annotate, never name the wrong
animal) is unchanged — only what powers the "does this look like the selected species"
judgment call changed.

## Actor + goal

Two changes to what a farmer sees after submitting a photo.

**1. Warn when the photo doesn't look like the selected species.** This was deliberately
deferred twice (`docs/DECISIONS.md`, M15's spec), on the stated grounds that a
wrong-species-but-real-animal photo "most likely comes back `uncertain`" anyway. **That
assumption was measured and is false.** Feeding 15 real cat photos to the cattle model with
`COW` selected:

- `uncertain` was returned **0 out of 15 times**;
- average confidence **71%**;
- individual results included **"Foot and Mouth Disease, 85%"** — a reportable disease,
  confidently, from a photo of a cat.

The mirror case is the same: cow photos through the cat model gave "Ringworm 90%", uncertain
only 3/15. So the existing behaviour is not a soft failure, it is a confident wrong answer,
and for FMD/LSD/PPR it is a confident wrong answer about a notifiable disease.

**2. Lead the result with what to do.** Today the card opens with a diagnosis and a
percentage, states the percentage again in a meter, and again in the explanation, and puts
the recommended action and next steps below all of it. The number is the least actionable
part.

## Boundaries & failure states

- **A mismatch blocks the diagnosis.** Revised after seeing it in use — see the
  "Revision" section at the end. The photo gets no disease prediction at all; the result slot
  shows a refusal instead.
- **The detector is the existing M15 species gate's model**, reused — no new dependency, no
  new dataset, no new download. It compares ImageNet probability mass across the four species
  groups this project supports.
- **Chosen by measurement, not by taste.** On 100 valid photos and 40 genuine mismatches:
  - naive top-5 class matching: **40% of valid FMD photos falsely flagged** — rejected;
  - top-1 with a confidence threshold: no operating point that both avoids false flags and
    catches anything — rejected;
  - normalised group-mass with `share < 0.02` and `total animal mass > 0.15`: **6% false
    warnings, 95% of real mismatches caught** — adopted.
- **False rejections are the accepted cost**, measured at 2.7% of valid photos. A rejection
  is recoverable — the message says what to do and the photo can be resubmitted — whereas a
  missed mismatch produces a confident, escalating diagnosis of the wrong animal.
- **No warning is emitted when the model has no opinion** (total animal mass at or below the
  floor) — close-up lesion photos often land there, and silence is correct for them.
- **Sheep is detectable but weak**: ImageNet has 3 cattle classes and 2 sheep classes against
  118 dog classes. The floor and share thresholds account for the imbalance, but a missed
  sheep/cow mismatch is expected and acceptable — this is a warning, not a guarantee.
- **`docs/DISCLAIMER.md`'s required wording is untouched.** "Likely X, confidence Y%" stays
  exactly as-is in the heading. Reducing percentage noise means removing the *duplicate*
  statements of the same number, never the required one.

## Examples

**Mismatch** — `species: "COW"`, photo of a cat → diagnosis proceeds, and the response
carries:
```json
{ "diagnosis": "Foot and Mouth Disease", "confidence": 0.85,
  "species_warning": "This photo looks like a cat, but Cow is selected. The result below is from the cattle model and may be meaningless — check the species and try again." }
```
The UI shows that above the result card.

**No mismatch** — a real cow photo with `COW` selected → `species_warning: null`, nothing
extra rendered.

**Close-up lesion photo** — the model has no confident species opinion → `species_warning:
null`. Silence, not a guess.

**Result card, after** — heading keeps `Likely: Foot and Mouth Disease (85% confidence)`,
then immediately **what to do**: the recommended action and next steps. Precautions follow.
The explanation moves below them as supporting detail. The confidence meter is removed; a
low-confidence result keeps a short worded caveat instead of a second percentage.

**Explanation text** — was `Predicted Foot and Mouth Disease with 100% confidence, based
primarily on: mouth_lesions, excessive_salivation, lameness.` (the percentage a third time,
and raw feature keys). Becomes `The strongest signs were mouth lesions, excessive salivation
and lameness.`

## Not in scope

- Blocking a submission on species mismatch.
- Training a species classifier. The existing pretrained model is reused as-is.
- Detecting species for symptom-based diagnosis — there is no photo to inspect.
- Changing any disease model, the disease lists, or the M15 not-an-animal gate.
- Removing the confidence value itself, which `docs/DISCLAIMER.md` requires.

## Acceptance criteria (must be checkable)

- [ ] A cat photo submitted with `COW` selected returns a non-null `species_warning` naming
      both the detected and the selected species, and still returns a diagnosis.
- [ ] A correct-species photo returns `species_warning: null`.
- [ ] Measured false-warning rate on valid photos stays at or below ~6%, and the caught rate
      on genuine mismatches at or above ~90%, on the same samples used to pick the thresholds.
- [ ] The warning renders above the results in the UI and is announced to screen readers.
- [ ] The result card shows the confidence percentage exactly **once**.
- [ ] Recommended action and next steps appear above the explanation in the DOM.
- [ ] The template explanation contains no percentage and no raw feature keys.
- [ ] All three suites pass; the app runs and is verified end to end in a browser.

## Agent mirror-back (fill before coding starts)

**Intent**: warn — not block — when a photo probably isn't the selected species, because the
current silent behaviour produces confident wrong diagnoses of notifiable diseases; and
restructure the result so the first thing read is the action, not the arithmetic.

**Inputs/outputs that change**:
- `ml-service` `POST /agent/diagnose` response gains `species_warning: string | null`.
- `backend` passes it through as `speciesWarning` on both diagnosis endpoints.
- `_template_explanation` drops the percentage and humanises feature names.

**Assumptions I had to make** (flagging rather than silently choosing):
1. **Warning, not block** — the request said "warning or message", and a 6% false-positive
   rate is tolerable for a message but not for a refusal.
2. **Thresholds are tuned on this project's own photo datasets**, so they are honest for these
   image distributions and not claimed to generalise.
3. **The warning is computed for image submissions only**, and only after the not-an-animal
   gate passes — a non-animal photo already has its own dedicated message.
4. **Confidence stays in the heading.** "Fewer percentages" is read as removing the second and
   third statements of the same number, not as overriding `docs/DISCLAIMER.md`.

## Revision (2026-09-23, same day): warn → block

Shipped as a warning first. The user immediately hit the case this was written for and it was
still wrong: a **dog photo with Cow selected** rendered the warning *and*, directly beneath
it, "Likely: Foot and Mouth Disease (60% confidence)" with "🚨 Escalate to vet — contact your
veterinarian or local animal health authority immediately; this is a reportable disease."

A caveat above a confident, escalating, wrong answer does not undo it. The reasoning for
warning-over-blocking — that a 6% false-positive rate was too high to refuse on — weighed the
wrong side: a false rejection is recoverable in one click, while a missed mismatch tells a
farmer to report a notifiable disease that isn't there.

**What changed**:

- `species_mismatch` is now a diagnosis value in its own right, mirroring M15's
  `invalid_image`: `confidence: 0.0`, `recommended_action: "retry_upload"`, no precautions, no
  next steps, and excluded from multi-photo agreement. The disease model never runs.
- The `species_warning` field is gone — the diagnosis value and its explanation carry it.
- Thresholds retuned for refusal: `share < 0.02` still, but **cow and sheep are now one
  group**. There is no sheep image model — sheep photos are deliberately routed to the cattle
  model (docs/DISCLAIMER.md) — so refusing a sheep photo for looking bovine would reject
  something the app supports by design. That alone removed a third of the false rejections.
- Measured after the change: **2.7% false rejections** of valid photos (close-up lesion shots,
  which is also why the message suggests a photo showing more of the animal), **84%** of
  dog-as-cow submissions refused.

**Verified end to end**, not just in tests: three separate dog photos with Cow selected each
returned `species_mismatch` / `retry_upload` / 0% / no guidance; a cat photo as Cow likewise;
and correct-species photos still diagnosed normally (cow FMD 89%, cow healthy 88%, cat
ringworm 48%, dog distemper 41%). In the browser the card reads "Wrong species for this
photo" with no disease named, no percentage, and no escalation block.

## Revision 2 (2026-09-23): the not-an-animal gate was the real hole

A screenshot of text uploaded with Dog selected came back "Kennel Cough, 42%" — it never
reached the species check, because M15's gate accepted it first. That gate asked whether any
of the top-5 classes was an animal, and 398 of ImageNet's 1000 classes are animals, so
cluttered images pass by chance.

Both checks were rebuilt on measurement:

- **Animal gate**: total probability mass over animal classes, threshold 0.30. Non-animals let
  through went from 2/12 to 0/12 at the same 2/90 cost in valid photos.
- **Species check**: each group scores by its **peak** class probability, not its summed mass.
  Summing gave dog an enormous structural advantage (118 classes against 5) and refused 7.5%
  of genuine cattle photos; dividing by class count over-corrected and dropped dog-as-cow
  detection to 7%. The peak is scale-free. Threshold 25, taken from the gap between the valid
  distribution (p95 ≈ 24) and genuine mismatches (median 98–170).

**Combined, measured**: 7.5% of valid photos refused; 87% of dog-as-cow, 93% of cat-as-cow,
and 100% of non-animal images refused.

**Known limitation, stated rather than hidden**: livestock photos submitted under Cat or Dog
are effectively not caught. The ratio distributions overlap with valid pet photos, so no
threshold separates them. This guards the common mistake — a pet photo under livestock — not
both directions.
