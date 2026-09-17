import { SYMPTOM_FIELDS } from './symptomFields'

export default function SymptomForm({
  tagNumber,
  farmId,
  symptoms,
  onTagNumberChange,
  onFarmIdChange,
  onSymptomChange,
  onSubmit,
  disabled,
}) {
  function handleSubmit(event) {
    event.preventDefault()
    onSubmit()
  }

  return (
    <form onSubmit={handleSubmit}>
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

      <fieldset disabled={disabled}>
        <legend>🩺 Symptoms</legend>
        <div className="symptom-grid">
          {SYMPTOM_FIELDS.map((field) => (
            <label key={field.key} htmlFor={field.key} className="symptom-chip">
              <input
                id={field.key}
                type="checkbox"
                checked={symptoms[field.key]}
                onChange={(event) => onSymptomChange(field.key, event.target.checked)}
              />
              <span aria-hidden="true">{field.icon}</span>
              {field.label}
            </label>
          ))}
        </div>
      </fieldset>

      <button type="submit" disabled={disabled}>
        {disabled ? '⏳ Submitting…' : '🐄 Get diagnosis'}
      </button>
    </form>
  )
}
