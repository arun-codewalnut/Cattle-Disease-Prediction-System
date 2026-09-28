// Buffalo has no model or dataset of its own. It's offered on the Symptoms screen only, using
// the cow model as a labelled approximation — docs/specs/buffalo-symptoms-cow-model.md.
export const SPECIES_OPTIONS = [
  { value: 'COW', label: 'Cow', icon: '🐄' },
  { value: 'BUFFALO', label: 'Buffalo', icon: '🐃' },
  { value: 'SHEEP', label: 'Sheep', icon: '🐑' },
  { value: 'GOAT', label: 'Goat', icon: '🐐' },
  { value: 'CAT', label: 'Cat', icon: '🐱' },
  { value: 'DOG', label: 'Dog', icon: '🐶' },
]

// Species offered on the Symptoms screen — the ones with a trained symptom model. Cow has the
// cattle model; Sheep and Goat share the PPR model (docs/specs/M12-sheep-disease-detection.md,
// docs/specs/goat-ppr-symptom-screen.md); Buffalo borrows the cow model. Cat/Dog: no usable
// symptom dataset exists, so they only appear on the Photo screen. ml-service enforces the
// same rule (DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES).
export const DIAGNOSIS_SUPPORTED_SPECIES = ['COW', 'BUFFALO', 'SHEEP', 'GOAT']

// Species offered on the Photo screen — all but Buffalo, which the cow photo model has never
// seen. Cat, Dog and Goat have their own photo models (M13/M14/M16); Sheep uses the cow model
// as a disclosed approximation.
export const PHOTO_SUPPORTED_SPECIES = ['COW', 'SHEEP', 'GOAT', 'CAT', 'DOG']

// Species diagnosed with another species' model. Every result for one of these carries a note
// saying so (DiagnosisResult.jsx). Matches ml-service's BORROWED_MODEL_SPECIES.
export const BORROWED_MODEL_NOTES = {
  BUFFALO:
    'Based on the cow model — trained on cattle cases, not buffalo. It can’t detect haemorrhagic septicaemia, a common buffalo disease, so check with a vet.',
}

// One-line capability summary shown under the species select, per screen — each sentence
// describes what *that* screen will do for the species, so there's no "Symptoms: … Photo: …"
// sentence the user has to parse. Accuracy figures: ml-service/models/REGISTRY.md.
export const SPECIES_SUMMARIES = {
  symptoms: {
    COW: 'Real symptom model — 5 cattle diseases, 89% accurate.',
    BUFFALO: 'No buffalo model exists yet — uses the cow model as an approximation.',
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
