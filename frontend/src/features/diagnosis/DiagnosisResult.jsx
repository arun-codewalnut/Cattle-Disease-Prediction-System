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
// applies to "this wasn't a valid photo." Its own treatment instead — but styled as a clear
// alert (red, same banner language as an escalate_to_vet result), not the neutral/greenish
// look it used to share with a healthy result. Nothing was wrong with the animal here, but
// something *did* go wrong with the submission, and it read as "all clear" before — a real
// point of confusion this fixes, not a cosmetic one.
function AttentionCard({ icon, heading, explanation }) {
  return (
    <section className="diagnosis-result diagnosis-result--attention">
      <div className="diagnosis-result__banner">
        <span className="diagnosis-result__icon" aria-hidden="true">
          {icon}
        </span>
        <div className="diagnosis-result__headline">
          <h2>{heading}</h2>
        </div>
      </div>
      <div className="diagnosis-result__body">
        {/* The explanation already ends with the concrete next step (retry / check species
            selection) — see app.agent.graph's _species_mismatch_message and
            _template_explanation in ml-service. Repeating it here would be the exact
            redundancy the diagnosis card's own confidence wording was already trimmed for. */}
        <p className="diagnosis-result__explanation">{explanation}</p>
      </div>
    </section>
  )
}

function InvalidImageCard({ result }) {
  return <AttentionCard icon="🚫" heading="Not a valid photo" explanation={result.explanation} />
}

// Same treatment, different cause: the photo is an animal, just not the selected one. No
// diagnosis was made, so rendering a confidence figure or a vet-triage badge would be
// inventing both. This replaced a warning shown *alongside* a real diagnosis, which left a
// dog photo reading "Foot and Mouth Disease, 60% — contact your veterinarian".
function SpeciesMismatchCard({ result }) {
  return <AttentionCard icon="🔄" heading="Wrong species for this photo" explanation={result.explanation} />
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
      {/* Banner: the two things worth a half-second glance — what it is, and how sure the
          model is — grouped together above everything else. The dial is a purely visual
          (non-numeric) read of confidence, not a second rendering of the percentage — that
          stays exactly once, in the heading below, per docs/DISCLAIMER.md's required
          "likely X, confidence Y%" wording (also what the existing tests match against, so
          the heading's text must stay a single unbroken string). */}
      <div className="diagnosis-result__banner">
        <span
          className={`diagnosis-result__icon${result.recommendedAction === 'monitor' ? ' diagnosis-result__icon--watching' : ''}`}
          aria-hidden="true"
        >
          {urgencyIcon}
        </span>
        <div className="diagnosis-result__headline">
          <h2>
            Likely: {result.diagnosis} ({confidencePercent}% confidence)
          </h2>
          <span
            className="confidence-dial"
            style={{ '--confidence': confidencePercent }}
            aria-hidden="true"
          />
        </div>
      </div>

      <div className="diagnosis-result__body">
        {lowConfidence && (
          <p className="confidence__caveat">
            <span aria-hidden="true">⚠️</span> Low confidence — treat this as a hint to look
            closer, not a finding.
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
