import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import DiagnosisIntake from './DiagnosisIntake'

function jsonResponse(ok, body) {
  return { ok, json: () => Promise.resolve(body) }
}

async function fillAndSubmit(user) {
  await user.type(screen.getByLabelText(/cattle tag number/i), 'COW-001')
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

  it('submits cattle + symptoms and renders the diagnosis result', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 1, tagNumber: 'COW-001', farmId: 42, createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(true, {
          id: 7,
          cattleId: 1,
          diagnosis: 'Foot and Mouth Disease',
          confidence: 0.81,
          explanation: 'Predicted Foot and Mouth Disease with 81% confidence.',
          recommendedAction: 'escalate_to_vet',
          createdAt: '2026-01-01T00:00:00Z',
        })
      )

    render(<DiagnosisIntake />)
    await fillAndSubmit(user)

    expect(await screen.findByText(/likely: foot and mouth disease \(81% confidence\)/i)).toBeInTheDocument()
    expect(screen.getByText(/escalate to vet/i)).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)

    const [cattleCall, diagnosisCall] = fetchMock.mock.calls
    expect(cattleCall[0]).toMatch(/\/api\/cattle$/)
    expect(diagnosisCall[0]).toMatch(/\/api\/cattle\/1\/diagnoses$/)
    expect(cattleCall[1].headers['X-Correlation-Id']).toBeTruthy()
  })

  it('shows an error and never submits symptoms when cattle creation fails', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(false, { code: 'CATTLE_TAG_DUPLICATE', message: 'Tag already exists.', details: null })
    )

    render(<DiagnosisIntake />)
    await fillAndSubmit(user)

    expect(await screen.findByRole('alert')).toHaveTextContent('Tag already exists.')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('shows an error when the diagnosis call fails after cattle creation succeeds', async () => {
    const user = userEvent.setup()
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(true, { id: 1, tagNumber: 'COW-001', farmId: 42, createdAt: '2026-01-01T00:00:00Z' })
      )
      .mockResolvedValueOnce(
        jsonResponse(false, { code: 'ML_SERVICE_UNAVAILABLE', message: 'ml-service is unreachable.', details: null })
      )

    render(<DiagnosisIntake />)
    await fillAndSubmit(user)

    expect(await screen.findByRole('alert')).toHaveTextContent('ml-service is unreachable.')
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
