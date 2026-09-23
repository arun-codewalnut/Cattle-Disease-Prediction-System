# Spec: Image diagnosis quality gate (mismatch/invalid-photo detection)

**Milestone**: M15
**Status**: in progress

> **Follow-up (2026-09-23): the species-match check this spec deferred now exists.** This
> milestone deliberately checked only "is it an animal at all", on the stated grounds that a
> wrong-species photo would come back `uncertain` anyway. Measured later, that was false — a
> cat photo submitted as a cow returned "Foot and Mouth Disease, 85%", and `uncertain` came
> back 0 times in 15. An advisory, non-blocking warning was added; the not-an-animal gate this
> spec specifies is unchanged and still runs first. See
> [species-mismatch-and-actionable-results.md](species-mismatch-and-actionable-results.md).
>
> **Follow-up 2 (2026-09-23): the top-5 rule was replaced.** `is_animal_photo` accepted a
> photo if *any* of its top-5 classes was an animal. With 398 of ImageNet's 1000 classes
> being animals, cluttered images passed by chance — a screenshot of text was diagnosed as
> "Kennel Cough, 42%". It now scores total probability mass over animal classes (≥ 0.30),
> which let through 0/12 non-animal test images versus the old rule's 2/12, at the same cost
> in valid photos. The gate's purpose and position in the graph are unchanged.

## Actor + goal

A farmer/vet uploads a photo for diagnosis. Today, every disease image model (cattle/cat/dog)
runs *any* uploaded photo straight through its classifier — none of them were trained to say
"I don't recognize this," so a photo of a car or a table could, in principle, receive a
confident-sounding disease label. This milestone adds a quality gate in front of every
image-diagnosis path (all species) so the user gets an honest, actionable response in three
distinct cases instead of one classifier blindly guessing on everything:

1. **Clear photo, confident diagnosis** — unchanged, already works.
2. **A real animal photo, but the disease classifier isn't confident about anything specific**
   — prompt to upload a clearer photo showing the affected area. This already existed as the
   "uncertain" diagnosis path; its explanation text was wrong for images (always said "not
   enough *symptom* information," nonsensical for a photo) — fixed here.
3. **Not a photo of an animal at all** (car, table, random object) — new: rejected before the
   disease classifier ever runs, with a distinct, clear "this doesn't look like an animal
   photo" message.

## Scope decision (confirmed with the user before coding)

Case 2 is **only** about symptom-confidence, not species identity — this gate does **not**
try to verify the uploaded photo is of the *correct* species (e.g. a dog photo submitted
while diagnosing a cat still passes the gate, since a dog is a real animal; it just likely
comes back "uncertain" from the cat disease classifier, same as today). Real per-species
verification was explicitly flagged as separate, bigger scope in a prior session
(`HANDOFF.md`) and stays out of scope here.

## Design: a free, zero-training "is this an animal" gate

Uses torchvision's pretrained (off-the-shelf, no fine-tuning) `MobileNet_V2_Weights.DEFAULT`
ImageNet-1k classifier — already a project dependency, ~14MB, cached after first download, no
new dataset or training run needed. Verified directly (not assumed) that the standard
ImageNet-1k class ordering groups every living-creature class (fish/bird/reptile/amphibian/
mammal/arachnid/insect/crustacean) contiguously at indices 0–397; index 398 ("abacus") onward
is the first man-made/object class.

`app/models/species_gate.py`'s `is_animal_photo()` checks the top-5 predictions (not just
top-1 — empirically, a real photo's single top guess can miss animal entirely; e.g. a real
dog photo's top-1 prediction was "web site," but its top-5 included 3 correct dog breeds) and
passes if *any* of them falls in the animal range. Verified against real data before wiring
this in:

- Real cattle/cat/dog photos (from this repo's own training data) — top-5 always includes at
  least one animal class, even when top-1 misses (3/3 tested, all passed).
- A real photo of a dining table and a real car photo (Wikimedia) — top-5 was 100% non-animal
  classes for both (0/5 each), correctly rejected.

## Examples

**Case 1 (happy path, unchanged)**: Cow photo with visible Lumpy Skin Disease nodules →
`{"diagnosis": "Lumpy Skin Disease", "confidence": 0.89, ...}`, escalates.

**Case 2 (unclear, image-aware messaging)**: A real but ambiguous/borderline cat photo →
`{"diagnosis": "uncertain", "confidence": 0.31, "explanation": "The photo didn't show a
clear, confident sign of any recognized condition. Try a clearer photo focused on the
affected area.", "recommended_action": "consult_vet"}`.

**Case 3 (new — invalid photo)**: A photo of a car →
`{"diagnosis": "invalid_image", "confidence": 0.0, "explanation": "This doesn't look like a
photo of an animal — please upload a clear photo of the animal itself.",
"recommended_action": "retry_upload"}`. Never reaches the species-specific disease model at
all. Rendered as its own distinct card style in the frontend (no fake confidence percentage
or vet-triage badge — those don't apply to "this wasn't a valid photo").

**Multi-photo submission**: `invalid_image` is a per-photo *result*, not a request-level HTTP
error — one bad photo in a 5-photo batch doesn't fail the other 4. This mirrors how
`"uncertain"` already works per-photo, and matters for the existing `diagnosesAgree` warning
(an `invalid_image` result should never be silently averaged into "agreement" with real
diagnoses — see acceptance criteria).

## Not in scope

- Verifying the uploaded photo matches the *selected* species (see "Scope decision" above).
- Any change to the symptom-diagnosis path (Cow, Sheep) — this is image-only.
- A confidence score or "how sure are we this isn't an animal" nuance — the gate is binary
  (animal-domain top-5 hit, or not), matching how simple this problem needs to be for a
  learning project.

## Acceptance criteria

- [x] `app/models/species_gate.py` — `is_animal_photo()`, verified against real animal photos
      (pass) and real non-animal photos (reject), not just unit-tested against synthetic data.
- [x] `predict_image_node` runs the gate before calling any species-specific disease model
      (Cow/Sheep/Cat/Dog all share the same gate — one implementation, not per-species).
- [x] `diagnosis: "invalid_image"` never reaches an LLM call or RAG retrieval (same
      "never call the LLM for a non-diagnosis state" principle as `"uncertain"`).
- [x] `recommended_action` for `invalid_image` is a new, distinct value (`retry_upload`), not
      reused from `escalate_to_vet`/`consult_vet`/`monitor` — those all imply a real diagnosis
      happened.
- [x] The pre-existing `"uncertain"` explanation text bug is fixed: it must describe *symptoms*
      when the submission was symptom-based, and *photo clarity* when it was image-based —
      previously always said "not enough symptom information," even for photos.
- [x] Frontend renders `invalid_image` with a distinct, dedicated visual style — no confidence
      percentage, no vet-action badge (see `species-unavailable`-style treatment).
- [x] Multi-photo batches: an `invalid_image` result is excluded from the `diagnosesAgree`
      comparison — it isn't a "diagnosis" to agree or disagree with; a batch with 4 real
      matching diagnoses and 1 invalid photo should not show a disagreement warning.
- [x] Works identically for all 4 image-diagnosable species (Cow, Sheep, Cat, Dog) — one
      shared gate, not species-specific logic.
- [x] Full test suite green across all three services, plus live end-to-end verification
      against the real running stack with a real non-animal photo.

## Agent mirror-back

**Intent**: add a quality gate in front of every image-diagnosis path so "not an animal at
all" gets a distinct, honest rejection instead of running through a classifier that was never
trained to recognize it, and fix the existing "uncertain" path's explanation text to make
sense for photos specifically — without attempting real species-match verification, which is
separate, larger, previously-deferred scope.

**Assumptions confirmed with the user before coding**: the middle tier ("unrelated picture")
means "real animal photo, just not a confident disease match" — not "wrong species entirely."
The latter would need a real per-species classifier, not just an animal/not-animal gate.
