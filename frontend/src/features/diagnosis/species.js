// Buffalo (M11) was removed as a supported species — see docs/specs/M11-buffalo-disease-detection.md's
// "Superseded" note: no usable buffalo dataset was ever found, so it never moved past a
// disclosed cow-model approximation.
export const SPECIES_OPTIONS = [
  { value: 'COW', label: 'Cow', icon: '🐄' },
  { value: 'SHEEP', label: 'Sheep', icon: '🐑' },
  { value: 'CAT', label: 'Cat', icon: '🐱' },
  { value: 'DOG', label: 'Dog', icon: '🐶' },
]

// M12 follow-up (docs/specs/M12-sheep-disease-detection.md): Sheep now has its own real,
// PPR-trained symptom model — no longer a cow-model approximation. Cat/Dog's symptom
// vocabulary still doesn't apply at all — SYMPTOM diagnosis stays blocked for them, enforced
// backend-side too (DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES on that endpoint).
export const DIAGNOSIS_SUPPORTED_SPECIES = ['COW', 'SHEEP']

// M13/M14 follow-up: Cat and Dog now have their own real, trained IMAGE models (see
// ml-service/app/models/cat_image_model.py, dog_image_model.py) — image-based diagnosis works
// for them even though symptom-based diagnosis (above) doesn't. Backend enforces this too.
export const IMAGE_ONLY_SUPPORTED_SPECIES = ['CAT', 'DOG']

// One-line capability summary per species, shown inline under the species select
// (AnimalIdentityFields.jsx). Condensed to a single line per species by request — this used
// to be paired with a separate, longer multi-sentence disclosure paragraph below it; that's
// gone now except for Dog, which keeps one short extra line (see AnimalIdentityFields.jsx)
// since "no Healthy class, treat as a hint only" is safety-relevant enough to say twice, not
// just cluttered repetition — a decision made and confirmed with the user in an earlier
// session (docs/DISCLAIMER.md, "shipped anyway, loudly disclosed").
export const SPECIES_SUMMARIES = {
  COW: 'Symptoms or photo — both real, trained models.',
  SHEEP: 'Symptoms: real PPR-only screen (negative result ≠ healthy). Photo: cow-model approximation.',
  CAT: 'Photo only — real, cat-specific model (Flea Allergy, Ringworm, Scabies, Healthy), 83% accurate.',
  DOG: 'Photo only — real model, but weak (~53% accurate) and has no Healthy option.',
}
