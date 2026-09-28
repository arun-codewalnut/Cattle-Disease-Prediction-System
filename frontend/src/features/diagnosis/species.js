// Buffalo (M11) was removed as a supported species — see docs/specs/M11-buffalo-disease-detection.md's
// "Superseded" note: no usable buffalo dataset was ever found, so it never moved past a
// disclosed cow-model approximation.
export const SPECIES_OPTIONS = [
  { value: 'COW', label: 'Cow', icon: '🐄' },
  { value: 'SHEEP', label: 'Sheep', icon: '🐑' },
  { value: 'GOAT', label: 'Goat', icon: '🐐' },
  { value: 'CAT', label: 'Cat', icon: '🐱' },
  { value: 'DOG', label: 'Dog', icon: '🐶' },
]

// M12 follow-up (docs/specs/M12-sheep-disease-detection.md): Sheep has its own real,
// PPR-trained symptom model — no longer a cow-model approximation. Goat shares it
// (docs/specs/goat-ppr-symptom-screen.md — the model was trained on goat and sheep records).
// Cat/Dog: no usable symptom dataset exists, so SYMPTOM diagnosis stays blocked for them,
// enforced server-side too (DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES on that endpoint).
export const DIAGNOSIS_SUPPORTED_SPECIES = ['COW', 'SHEEP', 'GOAT']

// M13/M14 follow-up: Cat and Dog have their own real, trained IMAGE models (see
// ml-service/app/models/cat_image_model.py, dog_image_model.py) — image-based diagnosis works
// for them even though symptom-based diagnosis (above) doesn't. ml-service enforces this too.
// (Goat was here too until it gained the PPR symptom screen above; its photo model — binary
// Healthy/Unhealthy — still works, since every symptom-diagnosable species also takes photos.)
export const IMAGE_ONLY_SUPPORTED_SPECIES = ['CAT', 'DOG']

// One-line capability summary per species, shown inline under the species select
// (SpeciesField.jsx). Condensed to a single line per species by request.
//
// M16 follow-up: Dog was retrained on a new dataset (70.5% accurate, now HAS a Healthy
// option) — the old "weak, no Healthy option" summary no longer applies.
export const SPECIES_SUMMARIES = {
  COW: 'Symptoms or photo — both real, trained models.',
  SHEEP: 'Symptoms: real PPR-only screen (negative result ≠ healthy). Photo: cow-model approximation.',
  GOAT: 'Symptoms: real PPR-only screen (negative result ≠ healthy). Photo: real model, but binary (Healthy/Unhealthy) — can’t name a specific disease.',
  CAT: 'Photo only — real, cat-specific model (Flea Allergy, Ringworm, Scabies, Healthy), 83% accurate.',
  DOG: 'Photo only — real, dog-specific skin-disease model (Bacterial Dermatosis, Fungal Infection, Hypersensitivity/Allergic Dermatosis, Healthy), 71% accurate.',
}
