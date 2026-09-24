// Shared by both the symptom-checklist and image-upload flows (SymptomForm.jsx,
// ImageUploadForm.jsx) — both need to know which species is being diagnosed.
//
// Was AnimalIdentityFields, which also collected a tag number and farm ID. Those were
// removed along with the whole animal record — neither ever reached the model, and the user
// shouldn't have to invent an ID to get a diagnosis. See
// docs/specs/remove-animal-identity.md. Species stays because it genuinely selects which
// trained model runs.
import { forwardRef } from 'react'
import { SPECIES_OPTIONS, SPECIES_SUMMARIES, DIAGNOSIS_SUPPORTED_SPECIES, IMAGE_ONLY_SUPPORTED_SPECIES } from './species'

// Ref forwarded to the <select> itself — DiagnosisIntake.jsx focuses it when the user clicks
// "Analyze with a different species," so the next thing to do is visually obvious rather than
// a silent state change somewhere off-screen.
const SpeciesField = forwardRef(function SpeciesField({ species, onSpeciesChange, disabled }, ref) {
  return (
    <div>
      <label htmlFor="species">
        <span aria-hidden="true">🔎 </span>
        Species
      </label>
      <select
        id="species"
        ref={ref}
        value={species}
        onChange={(event) => onSpeciesChange(event.target.value)}
        disabled={disabled}
      >
        {SPECIES_OPTIONS.map((option) => (
          <option key={option.value} value={option.value}>
            {option.icon} {option.label}
          </option>
        ))}
      </select>
      <p className="species-summary">{SPECIES_SUMMARIES[species]}</p>
      {!DIAGNOSIS_SUPPORTED_SPECIES.includes(species) && !IMAGE_ONLY_SUPPORTED_SPECIES.includes(species) && (
        <p className="species-disclaimer species-disclaimer--blocked">
          <span aria-hidden="true">🚧</span> Diagnosis isn't available yet for{' '}
          {SPECIES_OPTIONS.find((option) => option.value === species)?.label.toLowerCase()} —
          the cattle model's diseases don't apply to this species. This is tracked as
          future work.
        </p>
      )}
    </div>
  )
})

export default SpeciesField
