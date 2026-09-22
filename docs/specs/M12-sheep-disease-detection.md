# Spec: Sheep disease detection

**Milestone**: M12
**Status**: in progress

## Actor + goal

A farmer/vet with sheep can select "Sheep" in the species selector and get a diagnosis,
reusing the species architecture M11 already built — no new architecture decisions needed
here, per that milestone's own scoping intent.

## Disease-overlap research (confirmed via web research, not assumed)

- **Foot and Mouth Disease affects sheep** — same symptom family as cattle/buffalo (fever,
  vesicular lesions, salivation). One real, documented difference worth flagging: **sheep
  (and goats) frequently show little or no visible illness with FMD**, unlike cattle, which
  makes them a harder-to-detect transmission risk in practice. This doesn't change how the
  existing symptom checklist works, but it's worth knowing the checklist may under-trigger
  for a subclinically-infected sheep.
- **Foot rot is a common, genuinely sheep-specific disease** (bacterial hoof infection) —
  and it is **not represented anywhere in the current 5-disease list**
  (`ml-service/app/models/symptom_model.py`'s `DISEASES`). Unlike Buffalo (M11), where the
  existing classes were a reasonable approximation, Sheep has a real, common disease this
  model has no way to predict at all.
- **Sheep pox** (a distinct capripoxvirus disease, related to but not the same as Lumpy Skin
  Disease) is also a real, notifiable sheep disease not covered.

**What this means for scope**: the M11 pattern (reuse the cattle-trained model, disclose the
limitation) still applies, but the disclosure needs to be honest about a bigger gap for
sheep than it was for buffalo — the model can't represent foot rot or sheep pox at all, not
just "wasn't trained on sheep-specific data."

## No sheep-specific dataset found

Same outcome as M11's buffalo search: no confirmed downloadable sheep-disease symptom or
image dataset. Kaggle has sheep *detection* datasets (bounding boxes for locating sheep in
images), not disease classification. Consistent with M9/M11, this is flagged as follow-up
scope once a real dataset turns up, not solved here.

## Scope

- Add `SHEEP` to `Species` (backend enum) and `SPECIES_OPTIONS` (frontend) — no other
  architecture change, per this issue's own "not in scope."
- Strengthen the non-Cow disclosure text to mention that some diseases (foot rot, sheep pox)
  aren't represented by the model at all, not just "not trained on this species" — the
  Buffalo-era wording undersold the gap for Sheep specifically.

## Not in scope

- Cat/Dog (M13/M14).
- Any change to the species architecture itself established in M11.
- A real sheep-specific model — blocked on data (see above), same status as M9/M11's
  buffalo follow-up.

## Acceptance criteria

- [x] Spec written (this file) — sheep-relevant disease classes confirmed and documented
      (FMD overlap + subclinical-presentation nuance; foot rot and sheep pox flagged as
      real gaps, not assumed away).
- [x] `SHEEP` added to the `Species` enum and frontend `SPECIES_OPTIONS`.
- [x] Disclosure text updated to reflect the bigger gap for Sheep (some diseases aren't
      representable at all, not just "not trained on this species").
- [x] `docs/API_CONTRACTS.md` updated to list `SHEEP` as a valid `species` value.
- [x] Full build/test suite green across all three services — backend 18/18, ml-service
      unaffected (36/2 skipped), frontend lint + 10/10 + build — plus manual end-to-end
      verification against the real running stack: created a Sheep animal via
      `POST /api/animals`, confirmed the strengthened disclosure rendered, submitted
      FMD-indicative symptoms, and confirmed the diagnosis correctly escalated
      (`Foot and Mouth Disease`, `escalate_to_vet`) via the shared cattle-trained model.

## Agent mirror-back

**Intent**: extend M11's species pattern to a third species with no new architecture —
purely a data-point addition (enum value, dropdown option, sharper disclosure copy).

**Assumptions flagged before coding**:
1. The disclosure text is being generalized (not just swapping "buffalo" for "sheep") to
   also say some diseases aren't representable at all — this is a real, larger gap for
   sheep than for buffalo, and glossing over it with the exact same wording would understate
   the limitation.

## Follow-up: a real Sheep symptom model (2026-09-22)

**Buffalo (M11) was removed as a supported species** — see
`docs/specs/M11-buffalo-disease-detection.md`'s superseded note. No usable buffalo dataset
was ever found across two searches months apart; it never moved past the cow-model
approximation this spec's original scope also settled for. Rather than keep carrying a
species that could never become real, it was dropped.

**Sheep did get a real dataset this time**:
[PPR disease data from goats and sheep](https://www.kaggle.com/datasets/devothanyambo/ppr-disease-data-from-goats-and-sheep)
(Kaggle) — real field-collected clinical data from Northern Tanzania, RT-qPCR-confirmed
ground truth, not self-report. Full detail, including the real data-quality caveats (the
`animal`/`sex`/`age` columns are undocumented 0/1 encodings that couldn't be verified, so the
model is trained on the combined goat+sheep file rather than a guessed-at "sheep-only"
subset), is in `ml-service/data/sheep-symptoms/SOURCE.md`.

This is **not** the M11-pattern "reuse the cattle model" approximation anymore, and it's also
**not** a fix for the foot-rot/sheep-pox gap identified above — it's a third thing: a real,
narrowly-scoped model that screens for exactly one disease, **PPR (Peste des Petits
Ruminants)**, binary positive/negative. Symptom-based diagnosis for Sheep now routes to
`app/models/sheep_symptom_model.py` (a 6-feature XGBoost classifier, 80.5% CV accuracy, 78.8%
macro F1 — see `ml-service/models/REGISTRY.md`) instead of the cattle model. Foot rot and
sheep pox remain entirely unrepresented, same as before — that gap is unchanged, just now
sitting alongside a real PPR screen instead of a full cross-species approximation.

Photo-based diagnosis for Sheep is **unchanged** — still the cow image model, still a
disclosed approximation (no sheep-specific image dataset exists, PPR or otherwise).

**Updated acceptance criteria**:
- [x] Sheep symptom diagnosis routes to a real, trained model (`sheep_symptom_model.pkl`),
      not the cattle model — species is now forwarded on the symptom path too (it wasn't
      before this follow-up; only the image path was species-aware).
- [x] `REPORTABLE_DISEASES` includes the new PPR label (WOAH/OIE-notifiable, same escalation
      tier as FMD/LSD).
- [x] Frontend shows Sheep's own symptom checklist (`symptomFields.js`'s
      `SHEEP_SYMPTOM_FIELDS`), not the cattle checklist — the two models don't share a
      feature vocabulary at all.
- [x] Disclosure text rewritten to state the model's real, narrow scope (PPR only, not a
      "healthy" guarantee) rather than the old "reusing the cow model as an approximation"
      wording, which no longer applies to the symptom path.
- [x] `docs/API_CONTRACTS.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, `STATE.md`,
      `HANDOFF.md`, `README.md` updated; Buffalo removed from `Species` (backend enum),
      `SPECIES_OPTIONS` (frontend), and a Flyway migration added to clean up any existing
      `species = 'BUFFALO'` rows.
- [x] Full test suite green: backend 29/29, ml-service 50/2 skipped (RAG, same documented
      local blocker as always), frontend 13/13 + lint clean — plus manual end-to-end
      verification against the real running stack (backend + ml-service + browser UI): a real
      Sheep animal, real PPR-positive symptoms submitted through the actual form, correctly
      diagnosed and escalated.
