export const SPECIES_OPTIONS = [
  { value: 'COW', label: 'Cow', icon: '🐄' },
  { value: 'BUFFALO', label: 'Buffalo', icon: '🐃' },
  { value: 'SHEEP', label: 'Sheep', icon: '🐑' },
  { value: 'CAT', label: 'Cat', icon: '🐱' },
  { value: 'DOG', label: 'Dog', icon: '🐶' },
]

// M13/M14 (docs/specs/M13-cat-disease-detection.md, docs/specs/M14-dog-disease-detection.md):
// Buffalo/Sheep share the cattle model's disease family closely enough that reusing it is a
// disclosed approximation. Cat and Dog don't — the model's diseases and symptom vocabulary
// don't apply at all, so diagnosis is blocked entirely rather than producing a wrong-species
// result. Backend enforces this too (DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES), so this isn't just
// a UI-level restriction.
export const DIAGNOSIS_SUPPORTED_SPECIES = ['COW', 'BUFFALO', 'SHEEP']
