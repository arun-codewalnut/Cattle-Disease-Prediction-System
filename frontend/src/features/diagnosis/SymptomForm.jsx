export default function SymptomForm({ fields, symptoms, onSymptomChange, onSubmit, disabled }) {
  function handleSubmit(event) {
    event.preventDefault()
    onSubmit()
  }

  return (
    <form onSubmit={handleSubmit}>
      <fieldset disabled={disabled}>
        <legend>🩺 Symptoms</legend>
        <div className="symptom-grid">
          {fields.map((field) => (
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
        {disabled ? (
          <>
            <span className="btn-spinner" aria-hidden="true" /> Submitting…
          </>
        ) : (
          '🐄 Get diagnosis'
        )}
      </button>
    </form>
  )
}
