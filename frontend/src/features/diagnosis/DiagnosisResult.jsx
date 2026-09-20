const ACTION_LABELS = {
  escalate_to_vet: 'Escalate to vet',
  consult_vet: 'Consult a vet',
  monitor: 'Monitor',
}

const ACTION_ICONS = {
  escalate_to_vet: '🚨',
  consult_vet: '🩺',
  monitor: '👀',
}

function DiagnosisResultCard({ result }) {
  const confidencePercent = Math.round(result.confidence * 100)
  const isUrgent = result.recommendedAction === 'escalate_to_vet'
  const urgencyIcon = ACTION_ICONS[result.recommendedAction] ?? 'ℹ️'

  return (
    <section
      aria-live="polite"
      data-urgent={isUrgent}
      className={`diagnosis-result urgency-${result.recommendedAction}`}
    >
      <span className="diagnosis-result__icon" aria-hidden="true">
        {urgencyIcon}
      </span>
      <div>
        <h2>
          Likely: {result.diagnosis} ({confidencePercent}% confidence)
        </h2>
        <p>{result.explanation}</p>
        <p>
          <strong>Recommended action: </strong>
          <span className="action-badge">
            <span aria-hidden="true">{urgencyIcon}</span>
            <span role={isUrgent ? 'alert' : undefined}>
              {ACTION_LABELS[result.recommendedAction] ?? result.recommendedAction}
            </span>
          </span>
        </p>
        {result.precautions?.length > 0 && (
          <div className="guidance-block">
            <h3>
              <span aria-hidden="true">🛡️</span> Precautions
            </h3>
            <ul>
              {result.precautions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        )}
        {result.nextSteps?.length > 0 && (
          <div className="guidance-block">
            <h3>
              <span aria-hidden="true">📋</span> Next steps
            </h3>
            <ul>
              {result.nextSteps.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        )}
        <p className="disclaimer">
          <em>
            This is a probabilistic estimate, not a confirmed diagnosis. Always consult a vet
            before making treatment decisions.
          </em>
        </p>
      </div>
    </section>
  )
}

// Multi-photo follow-up: an image submission returns { results: [...], diagnosesAgree } —
// one card per photo, plus a warning banner when the photos didn't all get the same
// diagnosis. A symptom submission still returns a single result object, rendered as one card.
export default function DiagnosisResult({ result }) {
  if (!Array.isArray(result?.results)) {
    return <DiagnosisResultCard result={result} />
  }

  return (
    <div className="diagnosis-result-list">
      {!result.diagnosesAgree && (
        <p role="alert" className="diagnosis-disagreement-banner">
          <span aria-hidden="true">⚠️</span> These photos didn't all get the same diagnosis —
          see each result below rather than trusting just one.
        </p>
      )}
      {result.results.map((item, index) => (
        <DiagnosisResultCard key={item.id ?? index} result={item} />
      ))}
    </div>
  )
}
