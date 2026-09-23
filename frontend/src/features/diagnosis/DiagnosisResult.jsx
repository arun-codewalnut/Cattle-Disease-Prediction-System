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

// The percentage appears exactly once, in the heading, where docs/DISCLAIMER.md requires it
// ("likely X, confidence Y%"). The meter that used to sit under it was a second rendering of
// the same number, and the explanation stated it a third time — that redundancy is what was
// asked to go. What survives is the part a number alone doesn't convey: that a weak result
// should be treated as a hint. The Dog model genuinely sits in that band (52.6% accuracy, no
// Healthy class — see docs/DISCLAIMER.md).
const LOW_CONFIDENCE = 60

function isLowConfidence(confidencePercent) {
  return confidencePercent < LOW_CONFIDENCE
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

// Same treatment, different cause: the photo is an animal, just not the selected one. No
// diagnosis was made, so rendering a confidence figure or a vet-triage badge would be
// inventing both. This replaced a warning shown *alongside* a real diagnosis, which left a
// dog photo reading "Foot and Mouth Disease, 60% — contact your veterinarian".
function SpeciesMismatchCard({ result }) {
  return (
    <section className="diagnosis-result diagnosis-result--invalid-image">
      <span className="diagnosis-result__icon" aria-hidden="true">
        🔄
      </span>
      <div>
        <h2>Wrong species for this photo</h2>
        <p>{result.explanation}</p>
      </div>
    </section>
  )
}

function DiagnosisResultCard({ result }) {
  if (result.diagnosis === 'invalid_image') {
    return <InvalidImageCard result={result} />
  }
  if (result.diagnosis === 'species_mismatch') {
    return <SpeciesMismatchCard result={result} />
  }

  const confidencePercent = Math.round(result.confidence * 100)
  const isUrgent = result.recommendedAction === 'escalate_to_vet'
  const urgencyIcon = ACTION_ICONS[result.recommendedAction] ?? 'ℹ️'
  const lowConfidence = isLowConfidence(confidencePercent)

  return (
    <section data-urgent={isUrgent} className={`diagnosis-result urgency-${result.recommendedAction}`}>
      <span className="diagnosis-result__icon" aria-hidden="true">
        {urgencyIcon}
      </span>
      <div>
        {/* "likely X, confidence Y%" is required wording, not a stylistic choice — see
            docs/DISCLAIMER.md. It is also the only place a percentage appears. */}
        <h2>
          Likely: {result.diagnosis} ({confidencePercent}% confidence)
        </h2>

        {lowConfidence && (
          <p className="confidence__caveat">
            Low confidence — treat this as a hint to look closer, not a finding.
          </p>
        )}

        {/* What to do comes before why. The action and the steps are what someone standing
            in a field can act on; the reasoning is supporting detail and now sits below. */}
        <div className="next-actions">
          <p className="next-actions__headline">
            <span aria-hidden="true">{urgencyIcon}</span>{' '}
            <span role={isUrgent ? 'alert' : undefined}>
              {ACTION_LABELS[result.recommendedAction] ?? result.recommendedAction}
            </span>
          </p>
          {result.nextSteps?.length > 0 && (
            <ol className="next-actions__steps">
              {result.nextSteps.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
          )}
        </div>

        {result.precautions?.length > 0 && (
          <div className="guidance-block">
            <h3>
              <span aria-hidden="true">🛡️</span> Meanwhile
            </h3>
            <ul>
              {result.precautions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        <p className="diagnosis-result__explanation">{result.explanation}</p>
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
