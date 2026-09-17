const ACTION_LABELS = {
  escalate_to_vet: 'Escalate to vet',
  consult_vet: 'Consult a vet',
  monitor: 'Monitor',
}

export default function DiagnosisResult({ result }) {
  const confidencePercent = Math.round(result.confidence * 100)
  const isUrgent = result.recommendedAction === 'escalate_to_vet'

  return (
    <section aria-live="polite" data-urgent={isUrgent}>
      <h2>
        Likely: {result.diagnosis} ({confidencePercent}% confidence)
      </h2>
      <p>{result.explanation}</p>
      <p>
        <strong>Recommended action: </strong>
        <span role={isUrgent ? 'alert' : undefined}>
          {ACTION_LABELS[result.recommendedAction] ?? result.recommendedAction}
        </span>
      </p>
      <p>
        <em>
          This is a probabilistic estimate, not a confirmed diagnosis. Always consult a vet
          before making treatment decisions.
        </em>
      </p>
    </section>
  )
}
