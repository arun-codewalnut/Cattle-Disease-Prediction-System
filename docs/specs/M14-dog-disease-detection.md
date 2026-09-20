# Spec: Dog disease detection

**Milestone**: M14
**Status**: done — real Dog image model trained and wired in (see "Follow-up" section below,
including a real quality caveat this model carries)

## Actor + goal

A pet owner/vet can select "Dog" in the species selector — but, like Cat (M13), **cannot yet
submit a diagnosis for one**. This milestone applies M13's companion-animal framing to a second
species rather than re-deriving it, and resolves issue #23's dog-specific research (disease list,
dataset candidates) with real citations.

## Why this reuses M13's "block, don't approximate" decision

M13 (`docs/specs/M13-cat-disease-detection.md`) already argued the core judgment call: the
cattle-trained model's 5 disease classes (Foot and Mouth Disease, Lumpy Skin Disease, Mastitis,
Bovine Respiratory Disease, Healthy) and 11-field symptom vocabulary (`milk_yield_drop`,
`udder_swelling`, etc.) don't apply to a companion animal at all — predicting a livestock disease
for a pet would be actively wrong, not an imprecise approximation like Buffalo/Sheep reusing the
model is. **None of that reasoning is specific to cats** — it applies identically to Dog, so this
milestone doesn't re-litigate it, just applies the same decision: Dog is added as a selectable,
recorded species, and diagnosis submission is blocked for it at both the frontend and backend
layers, exactly as it is for Cat.

This is, per the user's explicit confirmation this session, more conservative than issue #23's
literal "source a dataset, train and wire in a dog-aware model" scope — the same gap M13 flagged
against issue #22's wording. Real dataset download and training remain explicit follow-up work,
not started here.

## Dog disease list — resolved via real web research (not invented)

Confirmed against veterinary references (AVMA, VCA, AKC), same bar M13 set for Cat. This list is
**not wired into any model in this milestone** — no dog model exists yet, same as Cat. Documented
so a future milestone doesn't have to re-research it:

- **Canine Distemper** — a contagious, often fatal viral disease attacking the respiratory,
  gastrointestinal, and nervous systems; airborne/contact spread. ~1 in 2 infected dogs die.
  Source: [AVMA — Canine distemper](https://www.avma.org/resources-tools/pet-owners/petcare/canine-distemper).
- **Canine Parvovirus ("parvo")** — highly contagious, attacks white blood cells and the GI
  tract; spread by direct contact or contaminated surfaces, environmentally persistent.
  Source: [AVMA — Canine parvovirus](https://www.avma.org/resources-tools/pet-owners/petcare/canine-parvovirus).
- **Kennel cough / Canine Infectious Respiratory Disease Complex (CIRDC)** — caused by a mix of
  bacteria/viruses (can include canine influenza); persistent cough in an otherwise-healthy-
  seeming dog, usually mild and self-limiting.
  Source: [AVMA — Disease risks for dogs in social settings](https://www.avma.org/resources-tools/pet-owners/petcare/disease-risks-dogs-social-settings).
- **Mange (sarcoptic and demodectic)** — parasitic skin disease. Sarcoptic mange (scabies,
  contagious, including to humans) and demodectic mange (not contagious) both cause hair loss,
  redness/crusting; onset areas and contagion differ by type.
  Sources: [VCA Animal Hospitals — Sarcoptic mange in dogs](https://vcahospitals.com/know-your-pet/mange-sarcoptic-in-dogs),
  [AKC — Mange in dogs](https://www.akc.org/expert-advice/health/mange-what-you-need-to-know/).
- Plus a `Healthy`/`uncertain` pair, matching the existing pattern.

## Escalation-equivalent for companion animals — already resolved, reused as-is

**Rabies.** M13 already researched and documented this as the companion-animal equivalent of
livestock's `REPORTABLE_DISEASES` — a legally mandatory veterinary reporting obligation for
suspected/confirmed rabies, and `docs/DISCLAIMER.md`'s "Companion animals (M13+)" section already
says **"cats and dogs"** explicitly, not just cats. No new decision needed here, and no edit to
`DISCLAIMER.md` is needed either — verified this session that the existing text is already
dog-inclusive throughout (see next section).

## Disclaimer/audience framing — confirmed, no edit needed

Re-read `docs/DISCLAIMER.md` this session: its "Companion animals (M13+)" section already covers
"companion animals (cat, dog)" and "cats and dogs" generically, and its "diagnosis is deliberately
blocked entirely for species without a real model" sentence already applies to any such species,
not just Cat. Unlike M13 (which added this section from scratch), **M14 makes no change to this
file** — it was written broadly enough the first time.

## Candidate datasets found, not downloaded

Web research this session found real candidates, **none downloaded or used** — downloading needs
the user's explicit go-ahead, same boundary M13 and M9 already established:

- Hugging Face `karenwky/pet-health-symptoms-dataset` — the same multi-species pet-symptoms
  dataset M13 flagged for Cat; would need filtering/verification for dog rows specifically.
- Kaggle `shijo96john/animal-disease-prediction` and `gracehephzibahm/animal-disease` —
  multi-species symptom/condition datasets; species coverage and licensing unverified.

No dog-specific image dataset turned up in this session's research (unlike M13, which found
Roboflow cat-skin/ringworm image sets) — worth another look if a future milestone picks this up.

## Boundaries & failure states

- `species: "DOG"` is a valid, storable value on `POST /api/animals` — creating a dog record
  works normally.
- `POST /api/animals/{id}/diagnoses` (or `.../diagnoses/image`) for a `DOG` animal returns a
  clean `400 DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES` error — never silently runs the cattle model
  and returns a cattle-disease name for a dog.
- Frontend: selecting Dog replaces the symptom/photo forms with the same "not available yet"
  message Cat already gets — no disabled-but-visible form that invites a doomed submission
  attempt.

## Examples

**Happy path**: `POST /api/animals` with `{"tagNumber": "DOG-001", "farmId": 5, "species": "DOG"}`
→ `201` with the created record. Selecting "Dog" in the frontend species dropdown replaces the
symptom checklist and photo upload with a "Diagnosis for Dog isn't available yet." message.

**Edge case**: `POST /api/animals/{id}/diagnoses` (or `.../diagnoses/image`) for that same dog
animal → `400 {"code": "DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES", "message": "Diagnosis isn't
available yet for species DOG.", "details": null}` — identical shape to the existing `CAT` case,
verified via direct `curl`, not just hidden in the UI.

## Not in scope

- Training or wiring in any real dog model — explicit follow-up, not started here (same call as
  M13 made for Cat).
- Downloading/evaluating the candidate datasets above — flagged, not fetched.
- Any change to Buffalo/Sheep/Cow/Cat behavior.
- Reworking M13's companion-animal framing — reused as-is; no gap found that would require it.
- Any other species — Dog is the last of the five from the original request
  (`docs/ROADMAP.md`'s "Target species" note).

## Acceptance criteria

- [x] Spec written, dog disease list and dataset candidates resolved with real research (this
      file).
- [x] `DOG` added to the `Species` enum and frontend `SPECIES_OPTIONS`.
- [x] Backend rejects a *symptom* diagnosis attempt for `DOG` with
      `DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES` — covered by a test. (Image diagnosis is now
      supported — see "Follow-up" below; this criterion covers the original symptom-only
      scope.)
- [x] Frontend originally showed the generic "not available yet" state for Dog — superseded by
      the Follow-up section's image-only UI, verified live there.
- [x] `docs/DISCLAIMER.md` reviewed and confirmed to already be dog-inclusive — no edit made,
      and that's a deliberate, documented decision, not an oversight.
- [x] `docs/API_CONTRACTS.md` updated: `DOG` as a valid `species` value, the rejection paragraph
      extended to cover both `CAT` and `DOG`, the error-code example list extended.
- [x] Full build/test suite green across all three services, plus manual end-to-end verification
      against the real running stack: created a Dog animal via `curl`, confirmed both diagnosis
      endpoints reject it with a clean `400 DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`, and in the real
      browser confirmed selecting Dog hides the symptom/photo forms (replaced by the "not
      available yet" block) while other species are unaffected. (Superseded for image
      diagnosis by the Follow-up section below.)

## Agent mirror-back

**Intent**: apply M13's already-settled companion-animal policy to a second species (Dog),
resolving issue #23's disease-list and dataset-sourcing research with real citations, without
re-deciding questions M13 already answered generally (rabies escalation, disclaimer framing).

**Assumptions flagged before coding**:
1. **Blocking diagnosis entirely for Dog, rather than sourcing a dataset and training a model
   this session, is a deliberate scope choice** — more conservative than issue #23's literal
   wording, mirroring the identical gap M13 flagged for issue #22. Confirmed explicitly with the
   user this session (not assumed) before starting implementation.
2. `docs/DISCLAIMER.md` is read-only this milestone — already written broadly enough in M13 to
   cover Dog without edits. Verified by rereading the file, not assumed from the M13 spec's
   description of it.
3. Dataset candidates found but not downloaded — same "ask before fetching" boundary as M13/M9.

## Follow-up: real Dog image model (this session) — a genuine quality caveat, not a clean win

A later session found `smadive/pet-disease-images` (Kaggle, anonymous download) with per-disease
folders matching this spec's researched list almost exactly:
`Distemper in Dog` (58), `Parvovirus in Dog` (82), `Kennel Cough in Dog` (82), `Mange in Dog` (71)
— 293 real photos. **No Healthy photos exist for Dog anywhere found**, in this dataset or any
other evaluated across any session — the trained model always names one of these 4 diseases, it
cannot say a dog is healthy. Disclosed prominently in the frontend and `docs/DISCLAIMER.md`, not
buried here alone.

Trained the same MobileNetV2-transfer-learning approach as M9/Cat (see
`ml-service/app/models/dog_image_model.py`, `ml-service/training/dog_image_model_train.py`),
including a legitimate attempt at improvement (horizontal-flip augmentation on the training
split only, val split untouched to avoid leakage) before accepting the result.

**Real result: 52.6% validation accuracy, 0.489 macro F1 — meaningfully weaker than Cat/Cow.**
Per-class F1: Mange 0.75 (decent), Canine Parvovirus 0.56, Kennel Cough 0.41, **Canine
Distemper 0.25** (worse than random for a 4-class problem). Likely cause, not just low sample
count: Mange is a visible skin condition with a strong photographic signature; Distemper/
Parvovirus/Kennel Cough are systemic/internal diseases that don't necessarily look
photographically distinct from each other or from a sick-but-undiagnosed dog. More of the same
kind of data likely wouldn't fix this on its own.

**Explicit decision, confirmed with the user rather than assumed**: ship it anyway, loudly
disclosed, rather than withholding it entirely or silently narrowing scope to just Mange. The
frontend (`AnimalIdentityFields.jsx`) shows this caveat prominently before a Dog photo is even
uploaded — accuracy number, which class is unreliable, and the no-Healthy-class gap — not a
footnote. `docs/DISCLAIMER.md` carries the same caveat.

Wired into `predict_image_node` (`ml-service/app/agent/graph.py`), routed by `species: "DOG"`,
same mechanism as Cat. Rabies escalation remains unimplemented as code for the same reason as
Cat: no Rabies class in the trained model.
