# Spec: Cat disease detection

**Milestone**: M13
**Status**: in progress

## Actor + goal

A pet owner/vet can select "Cat" in the species selector — but, unlike Buffalo/Sheep,
**cannot yet submit a diagnosis for one**. This milestone resolves the three open questions
issue #22 flagged (disease list, escalation-equivalent, disclaimer framing) and adds Cat as
a recorded species, while being explicit that real diagnosis is future work, not a "reuse
the cattle model as an approximation" situation like M11/M12.

## Why this milestone does NOT reuse the cattle model (the key decision)

M11/M12 reused the cattle-trained symptom model for Buffalo/Sheep because those species are
biologically close enough — cloven-hoofed livestock, overlapping diseases (FMD, LSD), and a
symptom vocabulary (fever, lesions, salivation, lameness) that transfers reasonably.

**None of that holds for Cat.** The model's 11 symptom fields include things like
`milk_yield_drop` and `udder_swelling` that are nonsensical for a cat. The model's 5 disease
classes (Foot and Mouth Disease, Lumpy Skin Disease, Mastitis, Bovine Respiratory Disease,
Healthy) don't include anything a cat actually gets — telling a cat owner their cat has
"Foot and Mouth Disease" wouldn't be an imperfect approximation, it would be **wrong in a
way that could genuinely mislead someone about their pet's health**. This is a materially
different risk than Buffalo/Sheep's "same disease family, unverified species-specificity."

**Decision**: Cat is added as a selectable species (for record-keeping / future-readiness),
but diagnosis submission is explicitly blocked for it — both in the frontend (no symptom
form or upload shown, a clear "not available yet" message instead) and in the backend
(`DiagnosisService` rejects a diagnosis attempt for an unsupported species with a dedicated
error code, so the restriction holds even if someone calls the API directly, not just
through the UI). This is more conservative than M11/M12, and deliberately so.

## Open questions from issue #22 — resolved here

**1. Disease list** (confirmed via web research, not invented): initial candidate list for
a future cat model —
- **Feline Upper Respiratory Infection (URI)** — feline calicivirus/herpesvirus, highly
  contagious cat-to-cat, signs: sneezing, ocular/nasal discharge, decreased appetite.
- **Ringworm** — fungal skin infection, hair loss, scaly/itchy skin.
- **FIV (Feline Immunodeficiency Virus)** — slow-progressing immune-system disease.
- Plus a `Healthy`/`uncertain` pair, matching the existing pattern.
This list is **not wired into any model in this milestone** — no cat model exists yet (see
below). It's documented here so a future milestone doesn't have to re-research it.

**2. Escalation-equivalent for companion animals**: **Rabies.** Confirmed via research:
veterinarians are under a **legal mandatory-reporting obligation** for suspected/confirmed
rabies in cats (and dogs) to local public-health authorities — a real, non-optional
equivalent to livestock's `REPORTABLE_DISEASES`, arguably with even higher stakes (rabies is
a fatal zoonotic disease). **Not implemented as code this milestone** — there's no active
cat diagnosis path to attach an escalation rule to yet. Documented so that whenever a real
cat model is built, "Rabies"/suspected rabies exposure must be added to a companion-animal
equivalent of `REPORTABLE_DISEASES` from day one, not bolted on after.

**3. Disclaimer/audience framing**: `docs/DISCLAIMER.md` is written for a farmer/vet
audience about livestock economics and herd management. A pet owner reading the same
document needs the same core guarantees (probabilistic estimate, not a diagnosis; always
escalate certain conditions) but the framing assumes a different context. Resolved by
adding a companion-animal-specific note to `docs/DISCLAIMER.md` now, even before a cat model
exists, so the document doesn't lag the species architecture.

## No cat-specific dataset downloaded (found candidates, not fetched)

Web research found real candidates worth a look, **none downloaded or used** — downloading
needs the user's explicit go-ahead, and picking one is a decision worth confirming, not
guessing:
- Kaggle "Pet Health Symptoms Dataset" (also mirrored on Hugging Face as
  `karenwky/pet-health-symptoms-dataset`) — text-described symptoms across multiple
  condition categories, multi-species (not cat-only, would need filtering/verification).
- Roboflow "Cat skin disease" (632 images) and "Cat ringworm" (122 images) — real image
  datasets, small.
- Kaggle "Animal Disease Prediction" / "cat skin disease" — multi-species or cat-specific,
  unverified licensing.
The Hugging Face mirror is worth checking first if this is picked up later — Hugging Face
`datasets` often don't require the Kaggle-style API-token dance, which has blocked M9's
cattle-image dataset for multiple sessions now.

## Boundaries & failure states

- `species: "CAT"` is a valid, storable value on `POST /api/animals` — creating a cat record
  works normally.
- `POST /api/animals/{id}/diagnoses` (or `.../diagnoses/image`) for a `CAT` animal returns a
  clean `400 DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES` error — never silently runs the cattle
  model and returns a cattle-disease name for a cat.
- Frontend: selecting Cat replaces the symptom/photo forms with a clear "not available yet"
  message — no disabled-but-visible form that invites a doomed submission attempt.

## Not in scope

- Dog (M14) — but should be lighter once this milestone's companion-animal framing exists,
  similar to how M12 was lighter after M11.
- Training or wiring in any real cat model — explicit follow-up, not started here.
- Downloading/evaluating the candidate datasets above — flagged, not fetched.
- Any change to Buffalo/Sheep/Cow behavior.

## Acceptance criteria

- [x] Spec written, all three issue #22 open questions resolved with real research (this
      file).
- [x] `CAT` added to the `Species` enum and frontend `SPECIES_OPTIONS`.
- [x] Backend rejects a diagnosis attempt for `CAT` (or any future non-diagnosis-supported
      species) with a dedicated `DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES` error — covered by a
      test, both for the symptom and image endpoints.
- [x] Frontend shows a clear "not available yet" state instead of the symptom/upload forms
      when Cat is selected — not a disabled form, an explicit message.
- [x] `docs/DISCLAIMER.md` updated with a companion-animal note (rabies as the
      escalation-equivalent, framing for a pet-owner audience).
- [x] `docs/API_CONTRACTS.md` updated: `CAT` as a valid `species` value, the new error code,
      and the "diagnosis not yet supported for this species" behavior.
- [x] Full build/test suite green across all three services — backend 21/21, ml-service
      unaffected (36/2 skipped), frontend lint + 11/11 + build — plus manual end-to-end
      verification against the real running stack: created a Cat animal via `curl`, directly
      confirmed both `POST /api/animals/{id}/diagnoses` and `.../diagnoses/image` reject it
      with a clean `400 DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`, and in the real browser
      confirmed selecting Cat hides the symptom/photo forms entirely (replaced by the "not
      available yet" block) while switching back to Cow correctly restores them.

## Agent mirror-back

**Intent**: resolve the architecture/policy questions this milestone needed answered
(disease list, escalation-equivalent, disclaimer framing) and add Cat as a species — without
pretending a nonsensical cattle-model prediction is a reasonable stand-in, the way it was
for Buffalo/Sheep.

**Assumptions flagged before coding**:
1. **Blocking diagnosis entirely for Cat, rather than reusing the cattle model, is the
   central judgment call of this milestone** — more conservative than issue #22's literal
   "train and wire in a cat-aware model" scope, but the alternative (predicting cattle
   diseases for cats) is a real correctness/safety problem, not a scoping shortcut.
2. Datasets found but not downloaded — same "ask before fetching" boundary as M9's Kaggle
   situation, flagged explicitly since real candidates exist this time (unlike M9/M11/M12
   where nothing concrete turned up).
3. `docs/DISCLAIMER.md` updated now even though no cat model exists yet — the document
   should describe the intended companion-animal policy (rabies escalation) before it's
   needed, not scramble to catch up once a model exists.
