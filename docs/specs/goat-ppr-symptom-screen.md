# Spec: Goat symptom diagnosis (PPR screen), and the symptom-dataset search

**Milestone**: stretch (post-M16)
**Status**: done

## Actor + goal

A goat keeper selects **Goat**, ticks the symptoms they see, and gets a real, trained screen
for **PPR (Peste des Petits Ruminants)** — today Goat symptom diagnosis is blocked outright
(`DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`), so the only option is a photo, whose model can say
"Unhealthy" but never name a disease.

PPR is primarily a goat disease, and the model Sheep already uses was trained on goat **and**
sheep field records together. This spec routes Goat symptoms to that same model.

## Why this model applies to goats (measured)

`data/sheep-symptoms/PPR-Goats-Sheep.csv` (21,199 records) mixes goat and sheep rows under an
`animal` column coded 0/1 that the dataset never documents, so rows can't be labelled goat or
sheep (see that folder's `SOURCE.md`). Instead of guessing, the model's out-of-fold accuracy
was measured per group, with the exact training setup (same XGBoost parameters, same 5-fold
split):

| `animal` | Rows | Accuracy | PPR recall | PPR precision |
|---|---|---|---|---|
| 0 | 8,045 | 80.0% | 78.9% | 84.9% |
| 1 | 13,154 | 80.7% | 87.9% | 84.6% |

Whichever code is goat, the model performs at the same level for it (~80% accuracy, ≥79% of
PPR cases caught) as it does overall — so using it for Goat is as justified as using it for
Sheep. No retraining; the committed `sheep_symptom_model.pkl` is used as-is.

## Symptom-dataset search (Sheep beyond PPR, Goat, Cat, Dog)

Searched the public Kaggle catalogue (2026-09-28) for goat/sheep/dog/cat/pet/livestock/
veterinary symptom data and inspected every candidate returned. None is usable to train a
diagnosis model:

| Dataset | Species | Why rejected |
|---|---|---|
| `researcher1548/livestock-symptoms-and-diseases` (43,778 rows) | cow, buffalo, sheep, goat | Generated, not recorded: each disease's symptom mix is identical to two decimals across all four species; "lumpy virus" and "pneumonia" have identical symptom profiles; 3,300+ sheep/goat rows labelled Lumpy Skin Disease, which doesn't infect sheep or goats; temperature is the same uniform range for every disease. |
| `shijo96john/animal-disease-prediction` (431 rows) | dog, cat, cow, sheep, goat, … | 39–75 rows per species across 13–28 disease names, many duplicates of one disease ("Bluetongue", "Blue Tongue Virus", …); the same symptom set labelled three unrelated diseases (e.g. goat vomiting + diarrhoea → arthritis-encephalitis, pleuropneumonia, coccidiosis). |
| `lolhaterbro/veteriary-clinical-dataset` (10,000 rows) | dog, cat | No disease column at all; symptoms are random (a dog with "drop in egg production"). |
| `gracehephzibahm/animal-disease` (871 rows) | many | No disease column — only a yes/no "Dangerous". |
| `sathwiknomula/animal-veterinary-health-dataset` (610 rows) | cat, goat, cow, dog, … | Pregnancy monitoring, no disease column, and scrambled columns ("Aggressive" as a discharge type). |
| `arsaljavaid78/digital-twin-goat-health-dataset` (8,907 rows) | goat | Wearable-sensor readings (heart rate, SpO₂, accelerometer) — nothing a farmer can tick as a symptom. |
| `maryam18/animal-disease-classification` (27 rows) | livestock | Disease descriptions, not cases. |

Decision per species:
- **Goat** — the real PPR data above (this spec).
- **Sheep** — unchanged: already on the same real PPR model; nothing found for its other
  diseases (foot rot, sheep pox, …).
- **Cat, Dog** — left out (owner's call): symptom diagnosis stays blocked. Not built from
  synthetic data — a companion-animal symptom model would also need a rabies escalation rule
  (docs/DISCLAIMER.md) designed before it ships.

## Boundaries & failure states

- Goat symptom diagnosis uses exactly Sheep's 6 PPR symptoms (`temp`, `nasal_discharge`,
  `diarrhea`, `difficult_breathing`, `eye_discharge`, `oral_nasal_lesion`) and returns
  `PPR (Peste des Petits Ruminants)` or `PPR Negative` — nothing else.
- A PPR-positive result **escalates to a vet**, exactly as for Sheep (PPR is already in
  `REPORTABLE_DISEASES`).
- "PPR Negative" means "not PPR", **not** "healthy" — the UI states this for Goat as it does
  for Sheep.
- Goat **photo** diagnosis is unchanged (the binary Healthy/Unhealthy image model).
- Cat and Dog symptom requests still return `400 DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`.

## Examples

```http
POST /api/diagnoses
{"species": "GOAT", "symptoms": {"nasal_discharge": true, "oral_nasal_lesion": true}}
```
→ `201`, `"species": "GOAT"`, `"diagnosis": "PPR (Peste des Petits Ruminants)"`,
`"recommendedAction": "escalate_to_vet"`.

All six symptoms `false` (what the UI sends when nothing is ticked) → `201`,
`"diagnosis": "PPR Negative"`. An empty `{}` means "no information" and returns `uncertain`,
same as every species.

`{"species": "CAT", "symptoms": {}}` → `400 DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES` (unchanged).

## Not in scope

- Retraining or changing the PPR model.
- Goat or Sheep diseases other than PPR; any Cat or Dog symptom model.
- Synthetic symptom data for any species.

## Acceptance criteria (must be checkable)

- [x] `POST /api/diagnoses` with `GOAT` returns 201 and a PPR result from the PPR model,
      escalating when positive.
- [x] The frontend shows Goat the 6 PPR symptoms and allows submission; its species summary
      says symptoms are a PPR-only screen.
- [x] Cat/Dog symptom requests are still rejected, server- and client-side.
- [x] ml-service and frontend tests cover the above and pass.
- [x] README, API_CONTRACTS, DISCLAIMER and the PPR dataset's SOURCE.md say Goat uses it.

## Agent mirror-back (fill before coding starts)

Route `GOAT` on the symptom path to the existing PPR model (one routing entry plus allowing
the species on the endpoint), give Goat the Sheep symptom checklist in the UI, and record the
dataset search so nobody repeats it. Assumption flagged and measured rather than taken on
trust: that the combined goat+sheep model performs acceptably for goats specifically.
