import { useEffect, useRef, useState } from 'react'
import { submitSymptoms, submitImage } from '../../api/diagnosisApi'
import { ApiError } from '../../api/client'
import SpeciesField from './SpeciesField'
import SymptomForm from './SymptomForm'
import ImageUploadForm from './ImageUploadForm'
import DiagnosisResult from './DiagnosisResult'
import { emptySymptoms, getSymptomFields } from './symptomFields'
import { DIAGNOSIS_SUPPORTED_SPECIES, IMAGE_ONLY_SUPPORTED_SPECIES, SPECIES_OPTIONS } from './species'

export default function DiagnosisIntake() {
  const [species, setSpecies] = useState('COW')
  const [symptoms, setSymptoms] = useState(emptySymptoms('COW'))
  const [images, setImages] = useState([])
  const [status, setStatus] = useState('idle') // idle | submitting | success | error
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  // Short summary spoken by the persistent live region below. A live region has to exist in
  // the DOM *before* its content changes, so it's always rendered and only its text changes
  // — mounting an aria-live node together with its content is the classic way to get silence.
  const [announcement, setAnnouncement] = useState('')
  const resultRef = useRef(null)
  const speciesFieldRef = useRef(null)

  // Sighted users on a phone had the same problem from the other direction: the result lands
  // below the fold, so submitting looked like nothing happened. Moving focus fixes the
  // screen-reader case and the scroll case at once.
  useEffect(() => {
    if (status !== 'success' || !resultRef.current) return
    resultRef.current.focus()
    resultRef.current.scrollIntoView?.({ behavior: 'smooth', block: 'start' })
  }, [status, result])

  function summarize(diagnosis) {
    if (Array.isArray(diagnosis?.results)) {
      const count = diagnosis.results.length
      return `${count} photo ${count === 1 ? 'result' : 'results'} ready.${
        diagnosis.diagnosesAgree ? '' : ' The photos did not all get the same diagnosis.'
      }`
    }
    if (diagnosis?.diagnosis === 'invalid_image') return 'That photo was not recognized as an animal.'
    return `Result ready. Likely ${diagnosis?.diagnosis}, ${Math.round((diagnosis?.confidence ?? 0) * 100)}% confidence.`
  }

  // Species deliberately survives a reset: the next animal is usually the same kind, on the
  // same farm, in the same session.
  function handleReset() {
    setSymptoms(emptySymptoms(species))
    setImages([])
    setResult(null)
    setError(null)
    setStatus('idle')
    setAnnouncement('Form cleared. Ready for a new check.')
  }

  // For when the result looks wrong for a reason other than the disease model itself — the
  // photo may have been the wrong species and the automatic check didn't catch it (that check
  // is a disclosed, imperfect heuristic — see docs/DISCLAIMER.md). Unlike handleReset, this
  // keeps the uploaded photo(s) so the user doesn't have to re-attach anything: only the
  // result/species selection clear, then focus moves to the species picker so the next step
  // is obvious.
  function handleTryDifferentSpecies() {
    setResult(null)
    setError(null)
    setStatus('idle')
    setAnnouncement('Pick the correct species and analyze the same photo again.')
    speciesFieldRef.current?.focus()
  }

  function handleSymptomChange(key, checked) {
    setSymptoms((prev) => ({ ...prev, [key]: checked }))
  }

  // Sheep's symptom vocabulary is completely different from cattle's (see
  // symptomFields.js) — switching species must reset to that species' own empty shape, not
  // carry over stale keys the new species' model wouldn't recognize.
  function handleSpeciesChange(nextSpecies) {
    setSpecies(nextSpecies)
    setSymptoms(emptySymptoms(nextSpecies))
  }

  async function handleSubmit() {
    setStatus('submitting')
    setError(null)
    setResult(null)

    const correlationId = crypto.randomUUID()

    try {
      const diagnosis = await submitSymptoms(species, symptoms, correlationId)
      setResult(diagnosis)
      setStatus('success')
      setAnnouncement(summarize(diagnosis))
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError('UNKNOWN_ERROR', 'Something went wrong.', null)
      setError(apiError)
      setStatus('error')
      setAnnouncement('')
    }
  }

  async function handleImageSubmit() {
    if (images.length === 0) {
      return
    }

    setStatus('submitting')
    setError(null)
    setResult(null)

    const correlationId = crypto.randomUUID()

    try {
      const diagnosis = await submitImage(species, images, correlationId)
      setResult(diagnosis)
      setStatus('success')
      setAnnouncement(summarize(diagnosis))
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError('UNKNOWN_ERROR', 'Something went wrong.', null)
      setError(apiError)
      setStatus('error')
      setAnnouncement('')
    }
  }

  const disabled = status === 'submitting'
  const diagnosisSupported = DIAGNOSIS_SUPPORTED_SPECIES.includes(species)
  const imageOnlySupported = IMAGE_ONLY_SUPPORTED_SPECIES.includes(species)

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Livestock symptom checker</h1>
        <p className="app-tagline">Quick symptom check for your herd, right from the field.</p>
      </header>

      <main className="diagnosis-card">
        <SpeciesField
          ref={speciesFieldRef}
          species={species}
          onSpeciesChange={handleSpeciesChange}
          disabled={disabled}
        />

        {diagnosisSupported && (
          <>
            <SymptomForm
              fields={getSymptomFields(species)}
              symptoms={symptoms}
              onSymptomChange={handleSymptomChange}
              onSubmit={handleSubmit}
              disabled={disabled}
            />

            <div className="form-divider" role="separator">
              <span>or</span>
            </div>
          </>
        )}

        {(diagnosisSupported || imageOnlySupported) && (
          <ImageUploadForm
            images={images}
            onImagesChange={setImages}
            onSubmit={handleImageSubmit}
            disabled={disabled}
          />
        )}

        {!diagnosisSupported && !imageOnlySupported && (
          <div className="species-unavailable">
            <span className="species-unavailable__icon" aria-hidden="true">
              🚧
            </span>
            <p>
              <strong>
                Diagnosis for {SPECIES_OPTIONS.find((option) => option.value === species)?.label} isn't
                available yet.
              </strong>
            </p>
            <p>This is tracked as future work — check back in a later update.</p>
          </div>
        )}

        {status === 'error' && error && (
          <p role="alert" className="form-error">
            <span aria-hidden="true">⚠️</span> {error.message}
          </p>
        )}

        {status === 'success' && result && (
          <div className="diagnosis-outcome" ref={resultRef} tabIndex={-1}>
            <DiagnosisResult result={result} />
            <div className="diagnosis-outcome__actions">
              {images.length > 0 && (
                <button type="button" className="retry-species-button" onClick={handleTryDifferentSpecies}>
                  <span aria-hidden="true">🔁</span> Analyze with a different species
                </button>
              )}
              <button type="button" className="reset-button" onClick={handleReset}>
                <span aria-hidden="true">↺</span> Start a new check
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Always mounted, empty until there's something to say. */}
      <div className="sr-only" role="status" aria-live="polite">
        {announcement}
      </div>
    </div>
  )
}
