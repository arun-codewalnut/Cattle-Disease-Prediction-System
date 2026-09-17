// Must match ml-service's FEATURES list exactly (app/models/symptom_model.py) — the two
// live in different languages/repos-within-a-repo with no shared schema, so keep these in
// sync by hand when the model's feature set changes.
export const SYMPTOM_FIELDS = [
  { key: 'fever', label: 'Fever' },
  { key: 'appetite_loss', label: 'Loss of appetite' },
  { key: 'nasal_discharge', label: 'Nasal discharge' },
  { key: 'milk_yield_drop', label: 'Drop in milk yield' },
  { key: 'mouth_lesions', label: 'Mouth lesions' },
  { key: 'lameness', label: 'Lameness' },
  { key: 'excessive_salivation', label: 'Excessive salivation' },
  { key: 'skin_nodules', label: 'Skin nodules' },
  { key: 'udder_swelling', label: 'Udder swelling' },
  { key: 'coughing', label: 'Coughing' },
  { key: 'labored_breathing', label: 'Labored breathing' },
]

export function emptySymptoms() {
  return Object.fromEntries(SYMPTOM_FIELDS.map((field) => [field.key, false]))
}
