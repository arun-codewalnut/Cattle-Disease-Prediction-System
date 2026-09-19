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

  it('submits animal + an uploaded photo and renders the placeholder diagnosis result', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 1, tagNumber: 'COW-001', farmId: 42, species: 'COW', createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(true, {
          id: 9,
          animalId: 1,
          diagnosis: 'Healthy',
          confidence: 0.5,
          explanation: 'This is a placeholder image-based prediction (Healthy, 50% confidence).',
          recommendedAction: 'monitor',
          createdAt: '2026-01-01T00:00:00Z',
        })
      )

    const image = new File(['fake-image-bytes'], 'cow.jpg', { type: 'image/jpeg' })

    render(<DiagnosisIntake />)
    await user.type(screen.getByLabelText(/animal tag number/i), 'COW-001')
    await user.type(screen.getByLabelText(/farm id/i), '42')
    await user.upload(screen.getByLabelText(/upload a photo/i), image)
    await user.click(screen.getByRole('button', { name: /diagnose from photo/i }))

    expect(await screen.findByText(/likely: healthy \(50% confidence\)/i)).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)

    const [animalCall, imageCall] = fetchMock.mock.calls
    expect(animalCall[0]).toMatch(/\/api\/animals$/)
    expect(imageCall[0]).toMatch(/\/api\/animals\/1\/diagnoses\/image$/)
    expect(imageCall[1].body).toBeInstanceOf(FormData)
    expect(imageCall[1].body.get('image')).toBe(image)
    expect(imageCall[1].headers['X-Correlation-Id']).toBeTruthy()
    // No Content-Type set manually — the browser must supply the multipart boundary itself.
    expect(imageCall[1].headers['Content-Type']).toBeUndefined()
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
    await user.upload(screen.getByLabelText(/upload a photo/i), image)
    await user.click(screen.getByRole('button', { name: /diagnose from photo/i }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Please enter an animal tag number.')
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('defaults species to Cow and shows no disclaimer', () => {
    render(<DiagnosisIntake />)

    expect(screen.getByLabelText(/species/i)).toHaveValue('COW')
    expect(screen.queryByText(/not trained on/i)).not.toBeInTheDocument()
  })

  it('shows the approximation disclosure and sends species when Buffalo is selected', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 2, tagNumber: 'BUF-001', farmId: 42, species: 'BUFFALO', createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(true, {
          id: 8,
          animalId: 2,
          diagnosis: 'Healthy',
          confidence: 0.9,
          explanation: 'Predicted Healthy with 90% confidence.',
          recommendedAction: 'monitor',
          precautions: [],
          nextSteps: [],
          createdAt: '2026-01-01T00:00:00Z',
        })
      )

    render(<DiagnosisIntake />)
    await user.selectOptions(screen.getByLabelText(/species/i), 'BUFFALO')

    expect(screen.getByText(/isn't trained on buffalo-specific data yet/i)).toBeInTheDocument()

    await user.type(screen.getByLabelText(/animal tag number/i), 'BUF-001')
    await user.type(screen.getByLabelText(/farm id/i), '42')
    await user.click(screen.getByLabelText(/fever/i))
    await user.click(screen.getByRole('button', { name: /get diagnosis/i }))

    await screen.findByText(/likely: healthy \(90% confidence\)/i)

    const [animalCall] = fetchMock.mock.calls
    expect(JSON.parse(animalCall[1].body)).toMatchObject({ species: 'BUFFALO' })
  })

  it('shows the species-gap disclosure and sends species when Sheep is selected', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 3, tagNumber: 'SHE-001', farmId: 11, species: 'SHEEP', createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(true, {
          id: 10,
          animalId: 3,
          diagnosis: 'uncertain',
          confidence: 0.2,
          explanation: 'Not enough symptom information was provided to make a confident prediction.',
          recommendedAction: 'consult_vet',
          precautions: [],
          nextSteps: [],
          createdAt: '2026-01-01T00:00:00Z',
        })
      )

    render(<DiagnosisIntake />)
    await user.selectOptions(screen.getByLabelText(/species/i), 'SHEEP')

    expect(screen.getByText(/isn't trained on sheep-specific data yet/i)).toBeInTheDocument()
    expect(screen.getByText(/sheep-only diseases aren't represented by it at all/i)).toBeInTheDocument()

    await user.type(screen.getByLabelText(/animal tag number/i), 'SHE-001')
    await user.type(screen.getByLabelText(/farm id/i), '11')
    await user.click(screen.getByLabelText(/fever/i))
    await user.click(screen.getByRole('button', { name: /get diagnosis/i }))

    await screen.findByText(/not enough symptom information was provided/i)

    const [animalCall] = fetchMock.mock.calls
    expect(JSON.parse(animalCall[1].body)).toMatchObject({ species: 'SHEEP' })
  })

  it('blocks diagnosis entirely for Cat instead of reusing the cattle model', async () => {
    const user = userEvent.setup()

    render(<DiagnosisIntake />)
    await user.selectOptions(screen.getByLabelText(/species/i), 'CAT')

    expect(screen.getByText(/diagnosis isn't available yet for cat/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /get diagnosis/i })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /diagnose from photo/i })).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/fever/i)).not.toBeInTheDocument()

    expect(fetchMock).not.toHaveBeenCalled()
  })
})
