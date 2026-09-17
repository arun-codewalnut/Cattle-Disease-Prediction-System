// Must match ml-service's FEATURES list exactly (app/models/symptom_model.py) — the two
// live in different languages/repos-within-a-repo with no shared schema, so keep these in
// sync by hand when the model's feature set changes.
export const SYMPTOM_FIELDS = [
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

export function emptySymptoms() {
  return Object.fromEntries(SYMPTOM_FIELDS.map((field) => [field.key, false]))
}
