import { useState } from 'react'
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
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError('UNKNOWN_ERROR', 'Something went wrong.', null)
      setError(apiError)
      setStatus('error')
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
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError('UNKNOWN_ERROR', 'Something went wrong.', null)
      setError(apiError)
      setStatus('error')
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
        <SpeciesField species={species} onSpeciesChange={handleSpeciesChange} disabled={disabled} />

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

        {status === 'success' && result && <DiagnosisResult result={result} />}
      </main>
    </div>
  )
}
