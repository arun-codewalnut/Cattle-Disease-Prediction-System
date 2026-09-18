// Shared by both the symptom-checklist and image-upload flows (SymptomForm.jsx,
// ImageUploadForm.jsx) — a diagnosis of either kind needs a cattle record to attach to.
export default function CattleIdentityFields({ tagNumber, farmId, onTagNumberChange, onFarmIdChange, disabled }) {
  return (
    <>
      <div>
        <label htmlFor="tagNumber">
          <span aria-hidden="true">🏷️ </span>
          Cattle tag number
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
