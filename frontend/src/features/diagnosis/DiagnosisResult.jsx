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

export default function DiagnosisResult({ result }) {
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
