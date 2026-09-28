// Shared by both screens (Symptoms and Photo) — both need to know which species is being
// diagnosed. Each screen passes its own list of species (only those it has a model for), so
// there's never an option that can't work.
//
// Was AnimalIdentityFields, which also collected a tag number and farm ID. Those were
// removed along with the whole animal record — neither ever reached the model, and the user
// shouldn't have to invent an ID to get a diagnosis. See
// docs/specs/remove-animal-identity.md. Species stays because it genuinely selects which
// trained model runs.
import { forwardRef } from 'react'
import { SPECIES_OPTIONS } from './species'

// Ref forwarded to the <select> itself — DiagnosisIntake.jsx focuses it after "New diagnosis",
// so the next thing to do is visually obvious rather than a silent state change.
const SpeciesField = forwardRef(function SpeciesField(
  { species, speciesValues, summary, onSpeciesChange, disabled },
  ref
) {
  return (
    <div className="species-field">
      <label htmlFor="species">
        {/* Step number, decorative — the label's accessible name stays just "Species". */}
        <span className="step-badge" aria-hidden="true">
          1
        </span>
        Species
      </label>
      <select
        id="species"
        ref={ref}
        value={species}
        onChange={(event) => onSpeciesChange(event.target.value)}
        disabled={disabled}
      >
        {SPECIES_OPTIONS.filter((option) => speciesValues.includes(option.value)).map((option) => (
          <option key={option.value} value={option.value}>
            {option.icon} {option.label}
          </option>
        ))}
      </select>
      <p className="species-summary">{summary}</p>
    </div>
  )
})

export default SpeciesField
