// Shared by both the symptom-checklist and image-upload flows (SymptomForm.jsx,
// ImageUploadForm.jsx) — a diagnosis of either kind needs an animal record to attach to.
// Renamed from CattleIdentityFields in M11 when species support was added — see
// docs/specs/M11-buffalo-disease-detection.md.
import { SPECIES_OPTIONS, DIAGNOSIS_SUPPORTED_SPECIES, IMAGE_ONLY_SUPPORTED_SPECIES } from './species'

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
        {species !== 'COW' && DIAGNOSIS_SUPPORTED_SPECIES.includes(species) && (
          <p className="species-disclaimer">
            <span aria-hidden="true">ℹ️</span> The diagnosis model isn't trained on{' '}
            {SPECIES_OPTIONS.find((option) => option.value === species)?.label.toLowerCase()}-specific
            data yet, and some {SPECIES_OPTIONS.find((option) => option.value === species)?.label.toLowerCase()}
            -only diseases aren't represented by it at all — results use the cattle model as
            an approximation and may miss species-specific conditions.
          </p>
        )}
        {species === 'CAT' && (
          <p className="species-disclaimer">
            <span aria-hidden="true">ℹ️</span> Symptom-based diagnosis isn't available for cat
            yet — but photo-based diagnosis is, using a real cat-specific model (Flea Allergy,
            Ringworm, Scabies, or Healthy).
          </p>
        )}
        {species === 'DOG' && (
          <p className="species-disclaimer species-disclaimer--low-confidence">
            <span aria-hidden="true">⚠️</span> Symptom-based diagnosis isn't available for dog
            yet — photo-based diagnosis is, but its real, measured accuracy is only about
            53%, barely better than guessing for 3 of its 4 diseases (Canine Distemper, Canine
            Parvovirus, Kennel Cough — only Mange is reliably recognized). It also has no
            "healthy" option — it will always name one of these 4 diseases, even for a
            healthy dog. Treat any dog photo result as a rough hint only, never a real
            diagnosis.
          </p>
        )}
        {!DIAGNOSIS_SUPPORTED_SPECIES.includes(species) && !IMAGE_ONLY_SUPPORTED_SPECIES.includes(species) && (
          <p className="species-disclaimer species-disclaimer--blocked">
            <span aria-hidden="true">🚧</span> Diagnosis isn't available yet for{' '}
            {SPECIES_OPTIONS.find((option) => option.value === species)?.label.toLowerCase()} —
            the cattle model's diseases don't apply to this species. This is tracked as
            future work.
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
