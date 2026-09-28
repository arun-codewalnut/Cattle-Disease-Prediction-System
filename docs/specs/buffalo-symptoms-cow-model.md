# Spec: Buffalo on the Symptoms screen, using the cow model (labelled approximation)

**Milestone**: stretch (post-M16), supersedes the Buffalo removal of 2026-09-22
**Status**: done

## Actor + goal

A buffalo keeper selects **Buffalo** on the **Symptoms** screen, ticks the signs they see, and
gets an estimate from the **cattle symptom model**. The screen says plainly, before and after
submitting, that this is a cow model standing in for a buffalo one.

Today Buffalo isn't offered at all. It was removed on 2026-09-22 (see
[M11-buffalo-disease-detection.md](M11-buffalo-disease-detection.md) and
[docs/DECISIONS.md](../DECISIONS.md)) because no buffalo dataset had been found. A third search
(2026-09-28) confirmed that is still true — two papers built buffalo symptom sets from
textbooks, but neither is downloadable. The owner chose a labelled estimate over nothing.

## Why the cow model is a reasonable stand-in, and where it isn't

- Buffalo and cattle are close relatives and share the diseases the cattle model knows. Foot
  and Mouth Disease looks much the same in both (fever, lameness, mouth and foot blisters).
- Lumpy Skin Disease is documented as less common in buffalo, so an LSD result is
  over-confident.
- Haemorrhagic septicaemia, a major cause of buffalo deaths, isn't one of the cattle model's
  five classes (Foot and Mouth Disease, Lumpy Skin Disease, Mastitis, Bovine Respiratory
  Disease, Healthy). A buffalo with it is matched to the nearest cattle disease.
- **Photos are not offered.** Buffalo skin is darker, thicker and less hairy; the cattle photo
  model has never seen one.

## Safeguards

1. **Symptoms screen only.** `BUFFALO` is in the symptom species list and not the photo one,
   in both the frontend and ml-service.
2. **Note before submitting**, under the species picker: the cow model is being used as an
   approximation.
3. **Note on every buffalo result**: the estimate comes from cattle cases, and haemorrhagic
   septicaemia can't be detected. The percentage stays, because it still drives the
   low-confidence caveat.
4. **Never "Monitor" for buffalo.** A result that would be `monitor` (a "Healthy" prediction)
   becomes `consult_vet`: a cow model saying a buffalo is healthy isn't strong enough to tell
   someone to just watch. `escalate_to_vet` for reportable diseases is unchanged.

## Boundaries & failure states

- `POST /api/diagnoses` with `species: "BUFFALO"` runs the cattle symptom model (the existing
  fallback in `_SYMPTOM_MODEL_BY_SPECIES`) and returns `species: "BUFFALO"`.
- `POST /api/diagnoses/image` with `species: "BUFFALO"` → 400
  `DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`, before any model runs.
- Switching to the Photo tab with Buffalo selected falls back to Cow, the same way Cat/Dog fall
  back when switching to Symptoms.
- `BUFFALO` is appended to the `Species` enum, never reordered (values are the wire format).

## Examples

```
POST /api/diagnoses
{"species": "BUFFALO", "symptoms": {"fever": true, "mouth_lesions": true, "lameness": true,
 "excessive_salivation": true, "appetite_loss": true}}
→ 201 {"species": "BUFFALO", "diagnosis": "Foot and Mouth Disease",
       "recommendedAction": "escalate_to_vet", ...}

POST /api/diagnoses  {"species": "BUFFALO", "symptoms": {}}   (model says Healthy)
→ 201 {"species": "BUFFALO", "diagnosis": "Healthy", "recommendedAction": "consult_vet", ...}
   (a Cow with the same symptoms gets "monitor")

POST /api/diagnoses/image  species=BUFFALO
→ 400 {"code": "DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES",
       "message": "Image-based diagnosis isn't available for species BUFFALO.", "details": null}
```

## Not in scope

- A buffalo-trained model, or any buffalo dataset work. If one of the paper authors shares
  their data, that's a new spec.
- Adding haemorrhagic septicaemia to the cattle model.
- Buffalo on the Photo screen.

## Acceptance criteria

- [x] Symptoms screen lists Buffalo (after Cow); Photo screen does not.
- [x] The species note for Buffalo says the cow model is used as an approximation.
- [x] A buffalo result shows a note that it's based on cattle cases and can't detect
      haemorrhagic septicaemia; a cow result doesn't.
- [x] ml-service accepts `BUFFALO` for symptoms (cattle model) and rejects it for photos with
      `DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`.
- [x] A buffalo "Healthy" result is `consult_vet`, a cow "Healthy" result is still `monitor`,
      and reportable diseases still escalate for both.
- [x] Frontend and ml-service tests cover each of the above; lint, build and e2e pass.

## Agent mirror-back

Intent: bring Buffalo back as an honest, labelled approximation on the symptom path only.
Inputs: species `BUFFALO` + the cattle symptom checklist. Outputs: the normal diagnosis
response, with `monitor` upgraded to `consult_vet`. Assumption: the result note is rendered by
the frontend from `species` in the response rather than added to the server's `explanation`,
so the explanation text stays the same for every species.
