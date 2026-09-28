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

// Species offered on the Symptoms screen — the ones with a trained symptom model. Cow has the
// cattle model; Sheep and Goat share the PPR model (docs/specs/M12-sheep-disease-detection.md,
// docs/specs/goat-ppr-symptom-screen.md). Cat/Dog: no usable symptom dataset exists, so they
// only appear on the Photo screen. ml-service enforces the same rule
// (DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES).
export const DIAGNOSIS_SUPPORTED_SPECIES = ['COW', 'SHEEP', 'GOAT']

// Species offered on the Photo screen — all five. Cat, Dog and Goat have their own photo
// models (M13/M14/M16); Sheep uses the cow model as a disclosed approximation.
export const PHOTO_SUPPORTED_SPECIES = SPECIES_OPTIONS.map((option) => option.value)

// One-line capability summary shown under the species select, per screen — each sentence
// describes what *that* screen will do for the species, so there's no "Symptoms: … Photo: …"
// sentence the user has to parse. Accuracy figures: ml-service/models/REGISTRY.md.
export const SPECIES_SUMMARIES = {
  symptoms: {
    COW: 'Real symptom model — 5 cattle diseases, 89% accurate.',
    SHEEP: 'Real PPR-only screen — a negative result means “not PPR”, not healthy.',
    GOAT: 'Real PPR-only screen — a negative result means “not PPR”, not healthy.',
  },
  photo: {
    COW: 'Real cattle photo model — Healthy, Lumpy Skin Disease, Foot and Mouth, Mastitis. 83% accurate.',
    SHEEP: 'No sheep photo model exists yet — uses the cow model as an approximation.',
    GOAT: 'Real model, but binary (Healthy/Unhealthy, 80% accurate) — can’t name a specific disease.',
    CAT: 'Real cat-specific model (Flea Allergy, Ringworm, Scabies, Healthy), 83% accurate.',
    DOG: 'Real dog-specific skin-disease model (Bacterial Dermatosis, Fungal Infection, Hypersensitivity/Allergic Dermatosis, Healthy), 71% accurate.',
  },
}
