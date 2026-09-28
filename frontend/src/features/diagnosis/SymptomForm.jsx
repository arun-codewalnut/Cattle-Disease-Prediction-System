export default function SymptomForm({ fields, symptoms, onSymptomChange, onSubmit, disabled }) {
  const tickedCount = fields.filter((field) => symptoms[field.key]).length

  function handleSubmit(event) {
    event.preventDefault()
    onSubmit()
  }

  return (
    <form onSubmit={handleSubmit}>
      <fieldset disabled={disabled}>
        <legend>
          <span className="step-badge" aria-hidden="true">
            2
          </span>
          What signs do you see?
        </legend>
        {/* Plain text, not a live region: the page's single polite live region is reserved
            for the result, and a second one here would talk over it on every tick. */}
        <p className={`symptom-count${tickedCount > 0 ? ' symptom-count--active' : ''}`}>
          {tickedCount === 0
            ? 'Tick everything you see'
            : `${tickedCount} ${tickedCount === 1 ? 'sign' : 'signs'} ticked`}
        </p>
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
