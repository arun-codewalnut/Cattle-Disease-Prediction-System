import { useState } from 'react'
import { createAnimal, submitSymptoms, submitImage } from '../../api/diagnosisApi'
import { ApiError } from '../../api/client'
import AnimalIdentityFields from './AnimalIdentityFields'
import SymptomForm from './SymptomForm'
import ImageUploadForm from './ImageUploadForm'
import DiagnosisResult from './DiagnosisResult'
import { emptySymptoms } from './symptomFields'
import { DIAGNOSIS_SUPPORTED_SPECIES, IMAGE_ONLY_SUPPORTED_SPECIES, SPECIES_OPTIONS } from './species'

export default function DiagnosisIntake() {
  const [tagNumber, setTagNumber] = useState('')
  const [farmId, setFarmId] = useState('')
  const [species, setSpecies] = useState('COW')
  const [symptoms, setSymptoms] = useState(emptySymptoms())
  const [image, setImage] = useState(null)
  const [status, setStatus] = useState('idle') // idle | submitting | success | error
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  function handleSymptomChange(key, checked) {
    setSymptoms((prev) => ({ ...prev, [key]: checked }))
  }

  // AnimalIdentityFields lives outside both <form> elements below (it's shared by both), so
  // the inputs' `required` attribute has no effect on either form's native submit validation
  // — validate explicitly instead of relying on that.
  function validateIdentityFields() {
    if (!tagNumber.trim()) {
      setError(new ApiError('TAG_NUMBER_REQUIRED', 'Please enter an animal tag number.', null))
      setStatus('error')
      return false
    }
    if (!farmId.toString().trim() || Number.isNaN(Number(farmId))) {
      setError(new ApiError('FARM_ID_REQUIRED', 'Please enter a valid farm ID.', null))
      setStatus('error')
      return false
    }
    return true
  }

  async function handleSubmit() {
    if (!validateIdentityFields()) {
      return
    }

    setStatus('submitting')
    setError(null)
    setResult(null)

    const correlationId = crypto.randomUUID()

    try {
      const animal = await createAnimal({ tagNumber, farmId, species }, correlationId)
      const diagnosis = await submitSymptoms(animal.id, symptoms, correlationId)
      setResult(diagnosis)
      setStatus('success')
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError('UNKNOWN_ERROR', 'Something went wrong.', null)
      setError(apiError)
      setStatus('error')
    }
  }

  async function handleImageSubmit() {
    if (!image || !validateIdentityFields()) {
      return
    }

    setStatus('submitting')
    setError(null)
    setResult(null)

    const correlationId = crypto.randomUUID()

    try {
      const animal = await createAnimal({ tagNumber, farmId, species }, correlationId)
      const diagnosis = await submitImage(animal.id, image, correlationId)
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
        <span className="app-logo" aria-hidden="true">🐄</span>
        <div>
          <h1>Livestock symptom checker</h1>
          <p className="app-tagline">🌾 Quick symptom check for your herd, right from the field.</p>
        </div>
      </header>

      <main className="diagnosis-card">
        <AnimalIdentityFields
          tagNumber={tagNumber}
          farmId={farmId}
          species={species}
          onTagNumberChange={setTagNumber}
          onFarmIdChange={setFarmId}
          onSpeciesChange={setSpecies}
          disabled={disabled}
        />

        {diagnosisSupported && (
          <>
            <SymptomForm
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
            image={image}
            onImageChange={setImage}
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
