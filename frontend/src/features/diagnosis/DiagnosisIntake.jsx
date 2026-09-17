import { useState } from 'react'
import { createCattle, submitSymptoms } from '../../api/diagnosisApi'
import { ApiError } from '../../api/client'
import SymptomForm from './SymptomForm'
import DiagnosisResult from './DiagnosisResult'
import { emptySymptoms } from './symptomFields'

export default function DiagnosisIntake() {
  const [tagNumber, setTagNumber] = useState('')
  const [farmId, setFarmId] = useState('')
  const [symptoms, setSymptoms] = useState(emptySymptoms())
  const [status, setStatus] = useState('idle') // idle | submitting | success | error
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  function handleSymptomChange(key, checked) {
    setSymptoms((prev) => ({ ...prev, [key]: checked }))
  }

  async function handleSubmit() {
    setStatus('submitting')
    setError(null)
    setResult(null)

    const correlationId = crypto.randomUUID()

    try {
      const cattle = await createCattle({ tagNumber, farmId }, correlationId)
      const diagnosis = await submitSymptoms(cattle.id, symptoms, correlationId)
      setResult(diagnosis)
      setStatus('success')
    } catch (err) {
      const apiError = err instanceof ApiError ? err : new ApiError('UNKNOWN_ERROR', 'Something went wrong.', null)
      setError(apiError)
      setStatus('error')
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <span className="app-logo" aria-hidden="true">🐄</span>
        <div>
          <h1>Cattle symptom checker</h1>
          <p className="app-tagline">🌾 Quick symptom check for your herd, right from the field.</p>
        </div>
      </header>

      <main className="diagnosis-card">
        <SymptomForm
          tagNumber={tagNumber}
          farmId={farmId}
          symptoms={symptoms}
          onTagNumberChange={setTagNumber}
          onFarmIdChange={setFarmId}
          onSymptomChange={handleSymptomChange}
          onSubmit={handleSubmit}
          disabled={status === 'submitting'}
        />

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
