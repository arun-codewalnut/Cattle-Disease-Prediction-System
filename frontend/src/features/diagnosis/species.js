export const SPECIES_OPTIONS = [
  { value: 'COW', label: 'Cow', icon: '🐄' },
  { value: 'BUFFALO', label: 'Buffalo', icon: '🐃' },
  { value: 'SHEEP', label: 'Sheep', icon: '🐑' },
  { value: 'CAT', label: 'Cat', icon: '🐱' },
  { value: 'DOG', label: 'Dog', icon: '🐶' },
]

// M13/M14 (docs/specs/M13-cat-disease-detection.md, docs/specs/M14-dog-disease-detection.md):
// Buffalo/Sheep share the cattle model's disease family closely enough that reusing it is a
// disclosed approximation, so both symptom-based AND image-based diagnosis work for them.
// Cat/Dog's symptom vocabulary still doesn't apply at all — SYMPTOM diagnosis stays blocked
// for them, enforced backend-side too (DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES on that endpoint).
export const DIAGNOSIS_SUPPORTED_SPECIES = ['COW', 'BUFFALO', 'SHEEP']

// M13/M14 follow-up: Cat and Dog now have their own real, trained IMAGE models (see
// ml-service/app/models/cat_image_model.py, dog_image_model.py) — image-based diagnosis works
// for them even though symptom-based diagnosis (above) doesn't. Backend enforces this too.
export const IMAGE_ONLY_SUPPORTED_SPECIES = ['CAT', 'DOG']
