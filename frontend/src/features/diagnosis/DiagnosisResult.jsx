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

// Bands are a visual encoding of the same percentage that's already in the heading — they
// add no clinical meaning the model didn't report. The point is that 91% and 53% currently
// look identical at a glance, and the Dog model genuinely sits near the bottom of that range
// (52.6% accuracy, no Healthy class — see docs/DISCLAIMER.md). A weak result should look
// weak, not just read weak.
// Banded on the *rounded* percentage, the same number the heading shows. Banding the raw
// value instead lets 0.798 render as "80% confidence" next to an amber "moderate" bar, which
// reads as a bug.
const LOW_CONFIDENCE = 60
const HIGH_CONFIDENCE = 80

function confidenceBand(confidencePercent) {
  if (confidencePercent >= HIGH_CONFIDENCE) return 'high'
  if (confidencePercent >= LOW_CONFIDENCE) return 'moderate'
  return 'low'
}

// M15 (docs/specs/M15-image-diagnosis-quality-gate.md): a photo that isn't of an animal at
// all never reached a disease model — rendering it through the normal card (a confidence
// percentage, a vet-triage badge) would be actively misleading, since neither concept
// applies to "this wasn't a valid photo." Deliberately its own simple treatment instead,
// matching SpeciesField's `.species-unavailable` visual language.
function InvalidImageCard({ result }) {
  return (
    <section className="diagnosis-result diagnosis-result--invalid-image">
      <span className="diagnosis-result__icon" aria-hidden="true">
        🚫
      </span>
      <div>
        <h2>Not a valid photo</h2>
        <p>{result.explanation}</p>
      </div>
    </section>
  )
}

function DiagnosisResultCard({ result }) {
  if (result.diagnosis === 'invalid_image') {
    return <InvalidImageCard result={result} />
  }

  const confidencePercent = Math.round(result.confidence * 100)
  const isUrgent = result.recommendedAction === 'escalate_to_vet'
  const urgencyIcon = ACTION_ICONS[result.recommendedAction] ?? 'ℹ️'
  const band = confidenceBand(confidencePercent)

  return (
    <section data-urgent={isUrgent} className={`diagnosis-result urgency-${result.recommendedAction}`}>
      <span className="diagnosis-result__icon" aria-hidden="true">
        {urgencyIcon}
      </span>
      <div>
        {/* "likely X, confidence Y%" is required wording, not a stylistic choice — see
            docs/DISCLAIMER.md. The meter below reinforces the number visually; it never
            replaces it. */}
        <h2>
          Likely: {result.diagnosis} ({confidencePercent}% confidence)
        </h2>

        <div className="confidence">
          <div className="confidence__track" aria-hidden="true">
            <div className={`confidence__fill confidence__fill--${band}`} style={{ width: `${confidencePercent}%` }} />
          </div>
          {band === 'low' && (
            <p className="confidence__caveat">
              Low confidence — treat this as a hint to look closer, not a finding.
            </p>
          )}
        </div>

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
      </div>
    </section>
  )
}

// One disclaimer per submission, not one per card. A five-photo result used to repeat the
// same paragraph five times, which trains people to skip exactly the sentence
// docs/DISCLAIMER.md needs them to read.
function ResultDisclaimer() {
  return (
    <p className="disclaimer">
      <em>
        This is a probabilistic estimate, not a confirmed diagnosis. Always consult a vet
        before making treatment decisions.
      </em>
    </p>
  )
}

// Multi-photo follow-up: an image submission returns { results: [...], diagnosesAgree } —
// one card per photo, plus a warning banner when the photos didn't all get the same
// diagnosis. A symptom submission still returns a single result object, rendered as one card.
export default function DiagnosisResult({ result }) {
  if (!Array.isArray(result?.results)) {
    return (
      <div className="diagnosis-result-list">
        <DiagnosisResultCard result={result} />
        <ResultDisclaimer />
      </div>
    )
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
      <ResultDisclaimer />
    </div>
  )
}
