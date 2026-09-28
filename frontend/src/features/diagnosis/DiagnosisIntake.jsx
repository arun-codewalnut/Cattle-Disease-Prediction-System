import { useEffect, useRef, useState } from 'react'
import { submitSymptoms, submitImage } from '../../api/diagnosisApi'
import { ApiError } from '../../api/client'
import SpeciesField from './SpeciesField'
import SymptomForm from './SymptomForm'
import ImageUploadForm from './ImageUploadForm'
import DiagnosisResult from './DiagnosisResult'
import { emptySymptoms, getSymptomFields } from './symptomFields'
import { DIAGNOSIS_SUPPORTED_SPECIES, PHOTO_SUPPORTED_SPECIES, SPECIES_SUMMARIES } from './species'

// Two screens, one toggle: the user picks how to get a diagnosis rather than scrolling past
// both forms. See docs/specs/two-screen-diagnosis-ui.md.
const MODES = [
  { id: 'symptoms', label: 'Symptoms', icon: '🩺', speciesValues: DIAGNOSIS_SUPPORTED_SPECIES },
  { id: 'photo', label: 'Photo', icon: '📷', speciesValues: PHOTO_SUPPORTED_SPECIES },
]

// Matches the CSS breakpoint where the result stops sitting beside the form and moves below
// it — only then does the page need scrolling to reach the result.
const STACKED_LAYOUT_QUERY = '(max-width: 899px)'

function isStackedLayout() {
  return typeof window !== 'undefined' && window.matchMedia?.(STACKED_LAYOUT_QUERY).matches === true
}

function ResultLoading({ mode, photoCount }) {
  const what = mode === 'photo' ? `${photoCount} ${photoCount === 1 ? 'photo' : 'photos'}` : 'symptoms'
  return (
    <div className="result-loading">
      <span className="result-loading__spinner" aria-hidden="true" />
      <p className="result-loading__text">Analysing {what}…</p>
      <div className="result-loading__skeleton" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
    </div>
  )
}

export default function DiagnosisIntake() {
  const [mode, setMode] = useState('symptoms')
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
  const tabRefs = useRef({})

  // Focus moves to the result so screen readers land on it. On a phone the result sits below
  // the form, so the page also scrolls there — otherwise submitting looks like nothing
  // happened. Side by side, it's already in view and scrolling would only jolt the page.
  useEffect(() => {
    if ((status !== 'success' && status !== 'error') || !resultRef.current) return
    resultRef.current.focus({ preventScroll: true })
    if (isStackedLayout()) {
      resultRef.current.scrollIntoView?.({ behavior: 'smooth', block: 'start' })
    }
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

  // Removes the result area, which puts the form panel back in the centre.
  function clearOutcome() {
    setResult(null)
    setError(null)
    setStatus('idle')
  }

  function handleModeChange(nextMode) {
    if (nextMode === mode) return
    setMode(nextMode)
    clearOutcome()
    setAnnouncement('')
    // Cat and Dog have no symptom model, so they aren't on the Symptoms screen.
    const allowed = MODES.find((m) => m.id === nextMode).speciesValues
    if (!allowed.includes(species)) {
      setSpecies('COW')
      setSymptoms(emptySymptoms('COW'))
    }
  }

  // Arrow keys move between tabs, as for any tab list (WAI-ARIA tabs pattern).
  function handleTabKeyDown(event) {
    const index = MODES.findIndex((m) => m.id === mode)
    const moves = { ArrowRight: 1, ArrowLeft: -1, Home: -index, End: MODES.length - 1 - index }
    if (!(event.key in moves)) return
    event.preventDefault()
    const next = MODES[(index + moves[event.key] + MODES.length) % MODES.length]
    handleModeChange(next.id)
    tabRefs.current[next.id]?.focus()
  }

  // The single post-result action: clears the result (and any error) *and* whatever was
  // submitted — symptoms and any uploaded photo(s) — so the form looks genuinely fresh, then
  // sends focus back to the species picker. Deliberately not "keep the photo, just change the
  // species": a wrong-species result means the uploaded photo was of the wrong animal in the
  // first place, so re-running the same photo against a different species model isn't a real
  // fix — the user needs to pick correctly and attach the right photo.
  function handleNewDiagnosis() {
    setSymptoms(emptySymptoms(species))
    setImages([])
    clearOutcome()
    setAnnouncement('Form cleared. Pick a species and check again.')
    speciesFieldRef.current?.focus()
  }

  function handleSymptomChange(key, checked) {
    setSymptoms((prev) => ({ ...prev, [key]: checked }))
  }

  // Sheep and Goat's symptom vocabulary is completely different from cattle's (see
  // symptomFields.js) — switching species must reset to that species' own empty shape, not
  // carry over stale keys the new species' model wouldn't recognize. A result for the old
  // species no longer describes what's on screen, so it goes too.
  function handleSpeciesChange(nextSpecies) {
    setSpecies(nextSpecies)
    setSymptoms(emptySymptoms(nextSpecies))
    clearOutcome()
  }

  async function runDiagnosis(request) {
    setStatus('submitting')
    setError(null)
    setResult(null)

    const correlationId = crypto.randomUUID()

    try {
      const diagnosis = await request(correlationId)
      setResult(diagnosis)
      setStatus('success')
      setAnnouncement(summarize(diagnosis))
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError('UNKNOWN_ERROR', 'Something went wrong.', null)
      console.error(`Diagnosis failed (correlation id ${correlationId}):`, apiError)
      setError(apiError)
      setStatus('error')
      setAnnouncement('')
    }
  }

  function handleSubmit() {
    return runDiagnosis((correlationId) => submitSymptoms(species, symptoms, correlationId))
  }

  function handleImageSubmit() {
    if (images.length === 0) return
    return runDiagnosis((correlationId) => submitImage(species, images, correlationId))
  }

  const disabled = status === 'submitting'
  const showResultArea = status !== 'idle'
  const activeMode = MODES.find((m) => m.id === mode)

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Animal health checker</h1>
        <p className="app-tagline">
          Find the likely disease from symptoms or photos — for cattle, sheep, goats, cats and dogs.
        </p>
      </header>

      <main className={`workspace${showResultArea ? ' workspace--split' : ''}`}>
        <div className="diagnosis-card">
          <div className="mode-tabs" role="tablist" aria-label="Diagnose from" onKeyDown={handleTabKeyDown}>
            {MODES.map((m) => (
              <button
                key={m.id}
                ref={(node) => {
                  tabRefs.current[m.id] = node
                }}
                type="button"
                role="tab"
                id={`tab-${m.id}`}
                aria-selected={mode === m.id}
                aria-controls={`panel-${m.id}`}
                tabIndex={mode === m.id ? 0 : -1}
                className="mode-tab"
                onClick={() => handleModeChange(m.id)}
                disabled={disabled}
              >
                <span aria-hidden="true">{m.icon}</span> {m.label}
              </button>
            ))}
          </div>

          <div role="tabpanel" id={`panel-${mode}`} aria-labelledby={`tab-${mode}`} className="mode-panel">
            <SpeciesField
              ref={speciesFieldRef}
              species={species}
              speciesValues={activeMode.speciesValues}
              summary={SPECIES_SUMMARIES[mode][species]}
              onSpeciesChange={handleSpeciesChange}
              disabled={disabled}
            />

            {mode === 'symptoms' ? (
              <SymptomForm
                fields={getSymptomFields(species)}
                symptoms={symptoms}
                onSymptomChange={handleSymptomChange}
                onSubmit={handleSubmit}
                disabled={disabled}
              />
            ) : (
              <ImageUploadForm
                images={images}
                onImagesChange={setImages}
                onSubmit={handleImageSubmit}
                disabled={disabled}
              />
            )}
          </div>
        </div>

        {showResultArea && (
          <section
            className="result-pane"
            aria-label="Diagnosis result"
            aria-busy={status === 'submitting'}
            ref={resultRef}
            tabIndex={-1}
          >
            <div className="result-pane__inner">
              {status === 'submitting' && <ResultLoading mode={mode} photoCount={images.length} />}

              {status === 'error' && error && (
                <div className="result-error">
                  <p role="alert" className="form-error">
                    <span aria-hidden="true">⚠️</span> {error.message}
                  </p>
                  <p className="result-error__hint">Check the form and try again.</p>
                </div>
              )}

              {status === 'success' && result && (
                <>
                  <DiagnosisResult result={result} />
                  <div className="diagnosis-outcome__actions">
                    <button type="button" className="new-diagnosis-button" onClick={handleNewDiagnosis}>
                      <span aria-hidden="true">🔄</span> New diagnosis
                    </button>
                  </div>
                </>
              )}
            </div>
          </section>
        )}
      </main>

      {/* Always mounted, empty until there's something to say. */}
      <div className="sr-only" role="status" aria-live="polite">
        {announcement}
      </div>
    </div>
  )
}
