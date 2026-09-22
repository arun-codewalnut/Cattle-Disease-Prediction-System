// Must match ml-service's cattle symptom model FEATURES list exactly
// (app/models/symptom_model.py) — the two live in different languages/repos-within-a-repo
// with no shared schema, so keep these in sync by hand when the model's feature set changes.
const CATTLE_SYMPTOM_FIELDS = [
  { key: 'fever', label: 'Fever', icon: '🤒' },
  { key: 'appetite_loss', label: 'Loss of appetite', icon: '🍽️' },
  { key: 'nasal_discharge', label: 'Nasal discharge', icon: '👃' },
  { key: 'milk_yield_drop', label: 'Drop in milk yield', icon: '🥛' },
  { key: 'mouth_lesions', label: 'Mouth lesions', icon: '👄' },
  { key: 'lameness', label: 'Lameness', icon: '🦵' },
  { key: 'excessive_salivation', label: 'Excessive salivation', icon: '💧' },
  { key: 'skin_nodules', label: 'Skin nodules', icon: '🔴' },
  { key: 'udder_swelling', label: 'Udder swelling', icon: '🐄' },
  { key: 'coughing', label: 'Coughing', icon: '😷' },
  { key: 'labored_breathing', label: 'Labored breathing', icon: '💨' },
]

// M12 follow-up (docs/specs/M12-sheep-disease-detection.md): a completely different symptom
// vocabulary from cattle's — must match app/models/sheep_symptom_model.py's FEATURES exactly.
// Sheep's real PPR model was trained on these 6 features only; nothing else it's ever seen.
const SHEEP_SYMPTOM_FIELDS = [
  { key: 'temp', label: 'Fever / high temperature', icon: '🤒' },
  { key: 'nasal_discharge', label: 'Nasal discharge', icon: '👃' },
  { key: 'diarrhea', label: 'Diarrhea', icon: '🤢' },
  { key: 'difficult_breathing', label: 'Difficult breathing', icon: '💨' },
  { key: 'eye_discharge', label: 'Eye discharge', icon: '👁️' },
  { key: 'oral_nasal_lesion', label: 'Sores in mouth or nose', icon: '👄' },
]

const SYMPTOM_FIELDS_BY_SPECIES = {
  SHEEP: SHEEP_SYMPTOM_FIELDS,
}

// Falls back to the cattle vocabulary for any species without its own (Cow, or any future
// species reusing the cattle model as an approximation) — same fallback pattern as
// ml-service's _SYMPTOM_MODEL_BY_SPECIES.
export function getSymptomFields(species) {
  return SYMPTOM_FIELDS_BY_SPECIES[species] ?? CATTLE_SYMPTOM_FIELDS
}

export function emptySymptoms(species) {
  return Object.fromEntries(getSymptomFields(species).map((field) => [field.key, false]))
}
