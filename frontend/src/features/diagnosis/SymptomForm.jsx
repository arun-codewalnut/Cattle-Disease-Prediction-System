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
        <label htmlFor="tagNumber">Cattle tag number</label>
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
        <label htmlFor="farmId">Farm ID</label>
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
        <legend>Symptoms</legend>
        {SYMPTOM_FIELDS.map((field) => (
          <div key={field.key}>
            <label htmlFor={field.key}>
              <input
                id={field.key}
                type="checkbox"
                checked={symptoms[field.key]}
                onChange={(event) => onSymptomChange(field.key, event.target.checked)}
              />
              {field.label}
            </label>
          </div>
        ))}
      </fieldset>

      <button type="submit" disabled={disabled}>
        {disabled ? 'Submitting…' : 'Get diagnosis'}
      </button>
    </form>
  )
}
