import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import DiagnosisIntake from './DiagnosisIntake'

// One fetch per submission. This suite used to mock two (create the animal, then diagnose
// against its id) — animal identity was removed, see docs/specs/remove-animal-identity.md.

function jsonResponse(ok, body) {
  return { ok, json: () => Promise.resolve(body) }
}

async function fillAndSubmit(user) {
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

  it('submits symptoms in a single call and renders the diagnosis result', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(true, {
        id: 7,
        species: 'COW',
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
    expect(fetchMock).toHaveBeenCalledTimes(1)

    const [diagnosisCall] = fetchMock.mock.calls
    expect(diagnosisCall[0]).toMatch(/\/api\/diagnoses$/)
    expect(diagnosisCall[1].headers['X-Correlation-Id']).toBeTruthy()
    expect(JSON.parse(diagnosisCall[1].body)).toMatchObject({ species: 'COW', symptoms: { fever: true } })
  })

  // Regression guard for docs/specs/remove-animal-identity.md: a diagnosis must never ask
  // for an identifier again. These inputs existed and were required before this change.
  it('asks for no animal tag number or farm ID', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(true, {
        id: 1, species: 'COW', diagnosis: 'Healthy', confidence: 0.95,
        explanation: 'Predicted Healthy.', recommendedAction: 'monitor',
        precautions: [], nextSteps: [], createdAt: '2026-01-01T00:00:00Z',
      })
    )

    render(<DiagnosisIntake />)

    expect(screen.queryByLabelText(/tag number/i)).not.toBeInTheDocument()
    expect(screen.queryByLabelText(/farm id/i)).not.toBeInTheDocument()

    // ...and a submission goes straight through without them.
    await fillAndSubmit(user)
    expect(await screen.findByText(/likely: healthy/i)).toBeInTheDocument()
  })

  it('shows an error when the diagnosis call fails', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(false, { code: 'ML_SERVICE_UNAVAILABLE', message: 'ml-service is unreachable.', details: null })
    )

    render(<DiagnosisIntake />)
    await fillAndSubmit(user)

    expect(await screen.findByRole('alert')).toHaveTextContent('ml-service is unreachable.')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('submits an uploaded photo and renders the diagnosis result', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(true, {
        results: [
          {
            id: 9,
            species: 'COW',
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
    await user.upload(screen.getByLabelText(/add photos/i), image)
    await user.click(screen.getByRole('button', { name: /diagnose from photo/i }))

    expect(await screen.findByText(/likely: healthy \(50% confidence\)/i)).toBeInTheDocument()
    expect(screen.queryByText(/didn't all get the same diagnosis/i)).not.toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(1)

    const [imageCall] = fetchMock.mock.calls
    expect(imageCall[0]).toMatch(/\/api\/diagnoses\/image$/)
    expect(imageCall[1].body).toBeInstanceOf(FormData)
    expect(imageCall[1].body.get('species')).toBe('COW')
    expect(imageCall[1].body.get('images')).toBe(image)
    expect(imageCall[1].headers['X-Correlation-Id']).toBeTruthy()
    // No Content-Type set manually — the browser must supply the multipart boundary itself.
    expect(imageCall[1].headers['Content-Type']).toBeUndefined()
  })

  it('submits up to 5 photos and shows a warning when their diagnoses disagree', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(true, {
        results: [
          {
            id: 1, species: 'CAT', diagnosis: 'Ringworm', confidence: 0.9,
            explanation: 'Predicted Ringworm.', recommendedAction: 'consult_vet',
            precautions: [], nextSteps: [], createdAt: '2026-01-01T00:00:00Z',
          },
          {
            id: 2, species: 'CAT', diagnosis: 'Scabies', confidence: 0.8,
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
    // Both photos in a single pick — the form takes a multi-file selection now.
    await user.upload(screen.getByLabelText(/add photos/i), [photo1, photo2])
    expect(screen.getByText(/2 of 5 selected/i)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /diagnose from photos/i }))

    expect(await screen.findByText(/didn't all get the same diagnosis/i)).toBeInTheDocument()
    expect(screen.getByText(/likely: ringworm/i)).toBeInTheDocument()
    expect(screen.getByText(/likely: scabies/i)).toBeInTheDocument()

    const [imageCall] = fetchMock.mock.calls
    expect(imageCall[1].body.get('species')).toBe('CAT')
    expect(imageCall[1].body.getAll('images')).toEqual([photo1, photo2])
  })

  it('renders an invalid-image photo distinctly, without a confidence or vet-action badge, and skips the disagreement banner', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(true, {
        results: [
          {
            id: 3, species: 'CAT', diagnosis: 'Ringworm', confidence: 0.9,
            explanation: 'Predicted Ringworm.', recommendedAction: 'consult_vet',
            precautions: [], nextSteps: [], createdAt: '2026-01-01T00:00:00Z',
          },
          {
            id: 4, species: 'CAT', diagnosis: 'invalid_image', confidence: 0.0,
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
    await user.upload(screen.getByLabelText(/add photos/i), [photo1, photo2])
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

  // The five "Add photo N" slots were replaced by one multi-select input — five affordances
  // for something the browser's file picker already does in one.
  it('takes several photos from a single pick, and appends on a second pick', async () => {
    const user = userEvent.setup()
    const a = new File(['a'], 'a.jpg', { type: 'image/jpeg' })
    const b = new File(['b'], 'b.jpg', { type: 'image/jpeg' })
    const c = new File(['c'], 'c.jpg', { type: 'image/jpeg' })

    render(<DiagnosisIntake />)

    // Only one file input, and it accepts multiple.
    expect(screen.queryByLabelText(/add photo 1/i)).not.toBeInTheDocument()
    expect(screen.getByLabelText(/add photos/i)).toHaveAttribute('multiple')

    await user.upload(screen.getByLabelText(/add photos/i), [a, b])
    expect(screen.getByText(/2 of 5 selected/i)).toBeInTheDocument()

    await user.upload(screen.getByLabelText(/add photos/i), c)
    expect(screen.getByText(/3 of 5 selected/i)).toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('keeps what fits and says how many were dropped when more than 5 are picked', async () => {
    const user = userEvent.setup()
    const files = Array.from({ length: 7 }, (_, i) =>
      new File([String(i)], `photo${i}.jpg`, { type: 'image/jpeg' })
    )

    render(<DiagnosisIntake />)
    await user.upload(screen.getByLabelText(/add photos/i), files)

    expect(screen.getByText(/5 of 5 selected/i)).toBeInTheDocument()
    // Silently swallowing the extras would leave the user thinking 7 were attached.
    expect(await screen.findByText(/2 photos not added/i)).toBeInTheDocument()
    expect(screen.getByText(/maximum 5 photos selected/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/add photos/i)).toBeDisabled()
  })

  it('lets a chosen photo be removed, which frees a slot again', async () => {
    const user = userEvent.setup()
    const a = new File(['a'], 'a.jpg', { type: 'image/jpeg' })
    const b = new File(['b'], 'b.jpg', { type: 'image/jpeg' })

    render(<DiagnosisIntake />)
    await user.upload(screen.getByLabelText(/add photos/i), [a, b])
    expect(screen.getByText(/2 of 5 selected/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /remove a\.jpg/i }))

    expect(screen.getByText(/1 of 5 selected/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /remove a\.jpg/i })).not.toBeInTheDocument()
  })

  // A live region has to exist before its content changes, or screen readers stay silent.
  // Focus moving to the result is what makes it discoverable for everyone else — on a phone
  // the result otherwise lands below the fold and submitting looks like nothing happened.
  it('announces the result and moves focus to it', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(true, {
        id: 7, species: 'COW', diagnosis: 'Foot and Mouth Disease', confidence: 0.81,
        explanation: 'Predicted FMD.', recommendedAction: 'escalate_to_vet',
        precautions: [], nextSteps: [], createdAt: '2026-01-01T00:00:00Z',
      })
    )

    render(<DiagnosisIntake />)

    // Present and empty before anything is submitted — that is the whole point.
    const live = document.querySelector('[aria-live="polite"]')
    expect(live).toBeInTheDocument()
    expect(live).toHaveTextContent('')

    await fillAndSubmit(user)
    await screen.findByText(/likely: foot and mouth disease/i)

    expect(live).toHaveTextContent(/likely foot and mouth disease, 81% confidence/i)
    expect(document.querySelector('.diagnosis-outcome')).toHaveFocus()
  })

  it('shows the disclaimer once for a multi-photo result, not once per card', async () => {
    const user = userEvent.setup()
    const card = (id, diagnosis) => ({
      id, species: 'CAT', diagnosis, confidence: 0.9, explanation: 'x',
      recommendedAction: 'consult_vet', precautions: [], nextSteps: [],
      createdAt: '2026-01-01T00:00:00Z',
    })
    fetchMock.mockResolvedValueOnce(
      jsonResponse(true, { results: [card(1, 'Ringworm'), card(2, 'Ringworm'), card(3, 'Ringworm')], diagnosesAgree: true })
    )

    render(<DiagnosisIntake />)
    await user.selectOptions(screen.getByLabelText(/species/i), 'CAT')
    await user.upload(screen.getByLabelText(/add photos/i), [
      new File(['a'], 'a.jpg', { type: 'image/jpeg' }),
      new File(['b'], 'b.jpg', { type: 'image/jpeg' }),
      new File(['c'], 'c.jpg', { type: 'image/jpeg' }),
    ])
    await user.click(screen.getByRole('button', { name: /diagnose from photos/i }))

    await screen.findAllByText(/likely: ringworm/i)
    expect(screen.getAllByText(/probabilistic estimate, not a confirmed diagnosis/i)).toHaveLength(1)
  })

  // docs/DISCLAIMER.md requires "likely X, confidence Y%" wording — the meter reinforces the
  // number, it must never replace it. The Dog model sits near this band in reality.
  it('flags a low-confidence result while keeping the required wording', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(true, {
        results: [{
          id: 1, species: 'DOG', diagnosis: 'Mange', confidence: 0.53, explanation: 'x',
          recommendedAction: 'consult_vet', precautions: [], nextSteps: [],
          createdAt: '2026-01-01T00:00:00Z',
        }],
        diagnosesAgree: true,
      })
    )

    render(<DiagnosisIntake />)
    await user.selectOptions(screen.getByLabelText(/species/i), 'DOG')
    await user.upload(screen.getByLabelText(/add photos/i), new File(['a'], 'a.jpg', { type: 'image/jpeg' }))
    await user.click(screen.getByRole('button', { name: /diagnose from photo/i }))

    expect(await screen.findByText(/likely: mange \(53% confidence\)/i)).toBeInTheDocument()
    expect(screen.getByText(/low confidence/i)).toBeInTheDocument()
  })

  it('clears the form for the next animal but keeps the species', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(true, {
        id: 1, species: 'COW', diagnosis: 'Healthy', confidence: 0.95, explanation: 'x',
        recommendedAction: 'monitor', precautions: [], nextSteps: [],
        createdAt: '2026-01-01T00:00:00Z',
      })
    )

    render(<DiagnosisIntake />)
    await fillAndSubmit(user)
    await screen.findByText(/likely: healthy/i)
    expect(screen.getByLabelText(/fever/i)).toBeChecked()

    await user.click(screen.getByRole('button', { name: /start a new check/i }))

    expect(screen.queryByText(/likely: healthy/i)).not.toBeInTheDocument()
    expect(screen.getByLabelText(/fever/i)).not.toBeChecked()
    // Same farm, same kind of animal — re-picking the species every time is busywork.
    expect(screen.getByLabelText(/species/i)).toHaveValue('COW')
  })

  it('renders real thumbnails and releases them when a photo is removed', async () => {
    const user = userEvent.setup()
    // jsdom has no Blob URL API, so the component falls back to an icon unless it's stubbed.
    const createObjectURL = vi.fn(() => 'blob:preview-1')
    const revokeObjectURL = vi.fn()
    vi.stubGlobal('URL', { ...URL, createObjectURL, revokeObjectURL })

    render(<DiagnosisIntake />)
    await user.upload(screen.getByLabelText(/add photos/i), new File(['a'], 'lesion.jpg', { type: 'image/jpeg' }))

    const thumb = document.querySelector('.photo-tray__thumb')
    expect(thumb).toHaveAttribute('src', 'blob:preview-1')
    expect(createObjectURL).toHaveBeenCalledTimes(1)

    // Leaking a full-size camera photo per re-pick is the failure mode this guards.
    await user.click(screen.getByRole('button', { name: /remove lesion\.jpg/i }))
    expect(revokeObjectURL).toHaveBeenCalledWith('blob:preview-1')
  })

  it('disables the photo submit button until a file is chosen', () => {
    render(<DiagnosisIntake />)

    expect(screen.getByRole('button', { name: /diagnose from photo/i })).toBeDisabled()
  })

  it('defaults species to Cow and shows no disclaimer', () => {
    render(<DiagnosisIntake />)

    expect(screen.getByLabelText(/species/i)).toHaveValue('COW')
    expect(screen.queryByText(/not trained on/i)).not.toBeInTheDocument()
  })

  it('shows the PPR-screen disclosure, uses sheep symptom fields, and sends species when Sheep is selected', async () => {
    const user = userEvent.setup()
    fetchMock.mockResolvedValueOnce(
      jsonResponse(true, {
        id: 10,
        species: 'SHEEP',
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

    await user.click(screen.getByLabelText(/nasal discharge/i))
    await user.click(screen.getByLabelText(/sores in mouth or nose/i))
    await user.click(screen.getByRole('button', { name: /get diagnosis/i }))

    await screen.findByText(/likely: ppr \(peste des petits ruminants\) \(93% confidence\)/i)
    expect(screen.getByText(/escalate to vet/i)).toBeInTheDocument()

    const [diagnosisCall] = fetchMock.mock.calls
    expect(JSON.parse(diagnosisCall[1].body)).toMatchObject({
      species: 'SHEEP',
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
    fetchMock.mockResolvedValueOnce(
      jsonResponse(true, {
        results: [
          {
            id: 20,
            species: 'CAT',
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
    const file = new File(['fake-image-bytes'], 'cat.jpg', { type: 'image/jpeg' })
    await user.upload(screen.getByLabelText(/add photos/i), file)
    await user.click(screen.getByRole('button', { name: /diagnose from photo/i }))

    await screen.findByText(/likely: ringworm/i)

    const [imageCall] = fetchMock.mock.calls
    expect(imageCall[1].body.get('species')).toBe('CAT')
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
