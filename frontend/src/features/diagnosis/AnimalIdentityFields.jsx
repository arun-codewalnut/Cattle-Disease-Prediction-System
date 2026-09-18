// Shared by both the symptom-checklist and image-upload flows (SymptomForm.jsx,
// ImageUploadForm.jsx) — a diagnosis of either kind needs an animal record to attach to.
// Renamed from CattleIdentityFields in M11 when species support was added — see
// docs/specs/M11-buffalo-disease-detection.md.
import { SPECIES_OPTIONS } from './species'

export default function AnimalIdentityFields({
  tagNumber,
  farmId,
  species,
  onTagNumberChange,
  onFarmIdChange,
  onSpeciesChange,
  disabled,
}) {
  return (
    <>
      <div>
        <label htmlFor="species">
          <span aria-hidden="true">🔎 </span>
          Species
        </label>
        <select
          id="species"
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
        {species !== 'COW' && (
          <p className="species-disclaimer">
            <span aria-hidden="true">ℹ️</span> The diagnosis model isn't trained on{' '}
            {SPECIES_OPTIONS.find((option) => option.value === species)?.label.toLowerCase()}-specific
            data yet — results use the cattle model as an approximation.
          </p>
        )}
      </div>

      <div>
        <label htmlFor="tagNumber">
          <span aria-hidden="true">🏷️ </span>
          Animal tag number
        </label>
        <input
          id="tagNumber"
          type="text"
          value={tagNumber}
          onChange={(event) => onTagNumberChange(event.target.value)}
          required
          disabled={disabled}
        />
      </div>

      <div>
        <label htmlFor="farmId">
          <span aria-hidden="true">🚜 </span>
          Farm ID
        </label>
        <input
          id="farmId"
          type="number"
          value={farmId}
          onChange={(event) => onFarmIdChange(event.target.value)}
          required
          disabled={disabled}
        />
      </div>
    </>
  )
}
