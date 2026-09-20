import { SPECIES_OPTIONS, SPECIES_SUMMARIES } from './species'

// Swaps instantly on species selection — inline emoji only, no downloaded imagery, matching
// the original cattle-farm UI redesign's convention (issue #15).
export default function SpeciesPreview({ species }) {
  const option = SPECIES_OPTIONS.find((o) => o.value === species)
  if (!option) {
    return null
  }

  return (
    <div className="species-preview" key={species}>
      <span className="species-preview__icon" aria-hidden="true">
        {option.icon}
      </span>
      <div>
        <p className="species-preview__name">{option.label}</p>
        <p className="species-preview__summary">{SPECIES_SUMMARIES[species]}</p>
      </div>
    </div>
  )
}
