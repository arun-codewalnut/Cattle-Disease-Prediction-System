import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import DiagnosisIntake from './DiagnosisIntake'

function jsonResponse(ok, body) {
  return { ok, json: () => Promise.resolve(body) }
}

async function fillAndSubmit(user) {
  await user.type(screen.getByLabelText(/animal tag number/i), 'COW-001')
  await user.type(screen.getByLabelText(/farm id/i), '42')
  await user.click(screen.getByLabelText(/fever/i))
  await user.click(screen.getByRole('button', { name: /get diagnosis/i }))
}

describe('DiagnosisIntake', () => {
  let fetchMock

  beforeEach(() => {
    fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('submits animal + symptoms and renders the diagnosis result', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 1, tagNumber: 'COW-001', farmId: 42, species: 'COW', createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(true, {
          id: 7,
          animalId: 1,
          diagnosis: 'Foot and Mouth Disease',
          confidence: 0.81,
          explanation: 'Predicted Foot and Mouth Disease with 81% confidence.',
          recommendedAction: 'escalate_to_vet',
          precautions: ['Isolate the affected animal from the rest of the herd immediately.'],
          nextSteps: ['Contact your veterinarian or local animal health authority immediately.'],
          createdAt: '2026-01-01T00:00:00Z',
        })
      )

    render(<DiagnosisIntake />)
    await fillAndSubmit(user)

    expect(await screen.findByText(/likely: foot and mouth disease \(81% confidence\)/i)).toBeInTheDocument()
    expect(screen.getByText(/escalate to vet/i)).toBeInTheDocument()
    expect(screen.getByText(/isolate the affected animal/i)).toBeInTheDocument()
    expect(screen.getByText(/contact your veterinarian or local animal health authority/i)).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)

    const [animalCall, diagnosisCall] = fetchMock.mock.calls
    expect(animalCall[0]).toMatch(/\/api\/animals$/)
    expect(diagnosisCall[0]).toMatch(/\/api\/animals\/1\/diagnoses$/)
    expect(animalCall[1].headers['X-Correlation-Id']).toBeTruthy()
    expect(JSON.parse(animalCall[1].body)).toMatchObject({ tagNumber: 'COW-001', farmId: 42, species: 'COW' })
  })

  it('shows an error and never submits symptoms when animal creation fails', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(false, { code: 'ANIMAL_TAG_DUPLICATE', message: 'Tag already exists.', details: null })
    )

    render(<DiagnosisIntake />)
    await fillAndSubmit(user)

    expect(await screen.findByRole('alert')).toHaveTextContent('Tag already exists.')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('shows an error when the diagnosis call fails after animal creation succeeds', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 1, tagNumber: 'COW-001', farmId: 42, species: 'COW', createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(false, { code: 'ML_SERVICE_UNAVAILABLE', message: 'ml-service is unreachable.', details: null })
      )

    render(<DiagnosisIntake />)
    await fillAndSubmit(user)

    expect(await screen.findByRole('alert')).toHaveTextContent('ml-service is unreachable.')
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('submits animal + an uploaded photo and renders the diagnosis result', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 1, tagNumber: 'COW-001', farmId: 42, species: 'COW', createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(true, {
          results: [
            {
              id: 9,
              animalId: 1,
              diagnosis: 'Healthy',
              confidence: 0.5,
              explanation: 'Predicted Healthy with 50% confidence.',
              recommendedAction: 'monitor',
              precautions: [],
              nextSteps: [],
              createdAt: '2026-01-01T00:00:00Z',
            },
          ],
          diagnosesAgree: true,
        })
      )

    const image = new File(['fake-image-bytes'], 'cow.jpg', { type: 'image/jpeg' })

    render(<DiagnosisIntake />)
    await user.type(screen.getByLabelText(/animal tag number/i), 'COW-001')
    await user.type(screen.getByLabelText(/farm id/i), '42')
    await user.upload(screen.getByLabelText(/add photo 1/i), image)
    await user.click(screen.getByRole('button', { name: /diagnose from photo/i }))

    expect(await screen.findByText(/likely: healthy \(50% confidence\)/i)).toBeInTheDocument()
    expect(screen.queryByText(/didn't all get the same diagnosis/i)).not.toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)

    const [animalCall, imageCall] = fetchMock.mock.calls
    expect(animalCall[0]).toMatch(/\/api\/animals$/)
    expect(imageCall[0]).toMatch(/\/api\/animals\/1\/diagnoses\/image$/)
    expect(imageCall[1].body).toBeInstanceOf(FormData)
    expect(imageCall[1].body.get('images')).toBe(image)
    expect(imageCall[1].headers['X-Correlation-Id']).toBeTruthy()
    // No Content-Type set manually — the browser must supply the multipart boundary itself.
    expect(imageCall[1].headers['Content-Type']).toBeUndefined()
  })

  it('submits up to 5 photos and shows a warning when their diagnoses disagree', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 1, tagNumber: 'CAT-001', farmId: 42, species: 'CAT', createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(true, {
          results: [
            {
              id: 1, animalId: 1, diagnosis: 'Ringworm', confidence: 0.9,
              explanation: 'Predicted Ringworm.', recommendedAction: 'consult_vet',
              precautions: [], nextSteps: [], createdAt: '2026-01-01T00:00:00Z',
            },
            {
              id: 2, animalId: 1, diagnosis: 'Scabies', confidence: 0.8,
              explanation: 'Predicted Scabies.', recommendedAction: 'consult_vet',
              precautions: [], nextSteps: [], createdAt: '2026-01-01T00:00:00Z',
            },
          ],
          diagnosesAgree: false,
        })
      )

    const photo1 = new File(['a'], 'a.jpg', { type: 'image/jpeg' })
    const photo2 = new File(['b'], 'b.jpg', { type: 'image/jpeg' })

    render(<DiagnosisIntake />)
    await user.selectOptions(screen.getByLabelText(/species/i), 'CAT')
    await user.type(screen.getByLabelText(/animal tag number/i), 'CAT-001')
    await user.type(screen.getByLabelText(/farm id/i), '42')
    await user.upload(screen.getByLabelText(/add photo 1/i), photo1)
    await user.upload(screen.getByLabelText(/add photo 2/i), photo2)
    expect(screen.getByText(/2 of 5 selected/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /diagnose from photos/i }))

    expect(await screen.findByText(/didn't all get the same diagnosis/i)).toBeInTheDocument()
    expect(screen.getByText(/likely: ringworm/i)).toBeInTheDocument()
    expect(screen.getByText(/likely: scabies/i)).toBeInTheDocument()

    const [, imageCall] = fetchMock.mock.calls
    expect(imageCall[1].body.getAll('images')).toEqual([photo1, photo2])
  })

  it('renders an invalid-image photo distinctly, without a confidence or vet-action badge, and skips the disagreement banner', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 4, tagNumber: 'CAT-002', farmId: 42, species: 'CAT', createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(true, {
          results: [
            {
              id: 3, animalId: 4, diagnosis: 'Ringworm', confidence: 0.9,
              explanation: 'Predicted Ringworm.', recommendedAction: 'consult_vet',
              precautions: [], nextSteps: [], createdAt: '2026-01-01T00:00:00Z',
            },
            {
              id: 4, animalId: 4, diagnosis: 'invalid_image', confidence: 0.0,
              explanation: "This doesn't look like a photo of an animal — please upload a clear photo of the animal itself.",
              recommendedAction: 'retry_upload', precautions: [], nextSteps: [], createdAt: '2026-01-01T00:00:00Z',
            },
          ],
          // Backend excludes invalid_image from the comparison — still "agree".
          diagnosesAgree: true,
        })
      )

    const photo1 = new File(['a'], 'a.jpg', { type: 'image/jpeg' })
    const photo2 = new File(['car'], 'car.jpg', { type: 'image/jpeg' })

    render(<DiagnosisIntake />)
    await user.selectOptions(screen.getByLabelText(/species/i), 'CAT')
    await user.type(screen.getByLabelText(/animal tag number/i), 'CAT-002')
    await user.type(screen.getByLabelText(/farm id/i), '42')
    await user.upload(screen.getByLabelText(/add photo 1/i), photo1)
    await user.upload(screen.getByLabelText(/add photo 2/i), photo2)
    await user.click(screen.getByRole('button', { name: /diagnose from photos/i }))

    expect(await screen.findByText(/likely: ringworm/i)).toBeInTheDocument()
    expect(screen.getByText(/not a valid photo/i)).toBeInTheDocument()
    expect(screen.getByText(/doesn't look like a photo of an animal/i)).toBeInTheDocument()
    expect(screen.queryByText(/didn't all get the same diagnosis/i)).not.toBeInTheDocument()
    // The invalid-image card must not show a fake confidence percentage or a vet-action badge
    // — both should appear exactly once each (the real Ringworm card only).
    expect(screen.getAllByText(/% confidence\)/i)).toHaveLength(1)
    expect(screen.getAllByText(/recommended action:/i)).toHaveLength(1)
  })

  it('disables the photo submit button until a file is chosen', () => {
    render(<DiagnosisIntake />)

    expect(screen.getByRole('button', { name: /diagnose from photo/i })).toBeDisabled()
  })

  it('rejects symptom submission with a blank tag number without calling the backend', async () => {
    const user = userEvent.setup()

    render(<DiagnosisIntake />)
    await user.type(screen.getByLabelText(/farm id/i), '42')
    await user.click(screen.getByLabelText(/fever/i))
    await user.click(screen.getByRole('button', { name: /get diagnosis/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Please enter an animal tag number.')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('rejects photo submission with a blank tag number without calling the backend', async () => {
    const user = userEvent.setup()
    const image = new File(['fake-image-bytes'], 'cow.jpg', { type: 'image/jpeg' })

    render(<DiagnosisIntake />)
    await user.type(screen.getByLabelText(/farm id/i), '42')
    await user.upload(screen.getByLabelText(/add photo 1/i), image)
    await user.click(screen.getByRole('button', { name: /diagnose from photo/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Please enter an animal tag number.')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('defaults species to Cow and shows no disclaimer', () => {
    render(<DiagnosisIntake />)

    expect(screen.getByLabelText(/species/i)).toHaveValue('COW')
    expect(screen.queryByText(/not trained on/i)).not.toBeInTheDocument()
  })

  it('shows the PPR-screen disclosure, uses sheep symptom fields, and sends species when Sheep is selected', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 3, tagNumber: 'SHE-001', farmId: 11, species: 'SHEEP', createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(true, {
          id: 10,
          animalId: 3,
          diagnosis: 'PPR (Peste des Petits Ruminants)',
          confidence: 0.93,
          explanation: 'Predicted PPR (Peste des Petits Ruminants) with 93% confidence.',
          recommendedAction: 'escalate_to_vet',
          precautions: [],
          nextSteps: [],
          createdAt: '2026-01-01T00:00:00Z',
        })
      )

    render(<DiagnosisIntake />)
    await user.selectOptions(screen.getByLabelText(/species/i), 'SHEEP')

    expect(screen.getByText(/real ppr-only screen/i)).toBeInTheDocument()
    // Cattle-only fields must be gone, replaced by sheep's own PPR symptom vocabulary.
    expect(screen.queryByLabelText(/mouth lesions/i)).not.toBeInTheDocument()
    expect(screen.getByLabelText(/sores in mouth or nose/i)).toBeInTheDocument()

    await user.type(screen.getByLabelText(/animal tag number/i), 'SHE-001')
    await user.type(screen.getByLabelText(/farm id/i), '11')
    await user.click(screen.getByLabelText(/nasal discharge/i))
    await user.click(screen.getByLabelText(/sores in mouth or nose/i))
    await user.click(screen.getByRole('button', { name: /get diagnosis/i }))

    await screen.findByText(/likely: ppr \(peste des petits ruminants\) \(93% confidence\)/i)
    expect(screen.getByText(/escalate to vet/i)).toBeInTheDocument()

    const [animalCall, diagnosisCall] = fetchMock.mock.calls
    expect(JSON.parse(animalCall[1].body)).toMatchObject({ species: 'SHEEP' })
    expect(JSON.parse(diagnosisCall[1].body)).toMatchObject({
      symptoms: { nasal_discharge: true, oral_nasal_lesion: true, temp: false },
    })
  })

  it('shows image-only diagnosis for Cat — no symptom form, but a real photo model', async () => {
    const user = userEvent.setup()

    render(<DiagnosisIntake />)
    await user.selectOptions(screen.getByLabelText(/species/i), 'CAT')

    expect(screen.getByText(/photo only.*cat-specific model/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /get diagnosis/i })).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/fever/i)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /diagnose from photo/i })).toBeInTheDocument()

    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('shows image-only diagnosis for Dog, with the weak-accuracy caveat in its one-line summary', async () => {
    const user = userEvent.setup()

    render(<DiagnosisIntake />)
    await user.selectOptions(screen.getByLabelText(/species/i), 'DOG')

    expect(screen.getByText(/photo only.*weak.*no healthy option/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /get diagnosis/i })).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/fever/i)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /diagnose from photo/i })).toBeInTheDocument()

    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('submits a Cat photo diagnosis end to end', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 9, tagNumber: 'CAT-001', farmId: 42, species: 'CAT', createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(true, {
          results: [
            {
              id: 20,
              animalId: 9,
              diagnosis: 'Ringworm',
              confidence: 0.91,
              explanation: 'Predicted Ringworm with 91% confidence.',
              recommendedAction: 'consult_vet',
              precautions: [],
              nextSteps: [],
              createdAt: '2026-01-01T00:00:00Z',
            },
          ],
          diagnosesAgree: true,
        })
      )

    render(<DiagnosisIntake />)
    await user.selectOptions(screen.getByLabelText(/species/i), 'CAT')
    await user.type(screen.getByLabelText(/animal tag number/i), 'CAT-001')
    await user.type(screen.getByLabelText(/farm id/i), '42')
    const file = new File(['fake-image-bytes'], 'cat.jpg', { type: 'image/jpeg' })
    await user.upload(screen.getByLabelText(/add photo 1/i), file)
    await user.click(screen.getByRole('button', { name: /diagnose from photo/i }))

    await screen.findByText(/likely: ringworm/i)

    const [animalCall] = fetchMock.mock.calls
    expect(JSON.parse(animalCall[1].body)).toMatchObject({ species: 'CAT' })
  })
})
