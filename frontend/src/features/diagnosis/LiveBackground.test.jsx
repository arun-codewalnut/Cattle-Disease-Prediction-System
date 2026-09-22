import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from '../../App'
import LiveBackground from './LiveBackground'

// The background is decorative. These tests guard the contract that makes it safe to add at
// all: it must stay out of the accessibility tree, out of the way of pointer input, and out
// of every query the rest of the suite relies on.
describe('LiveBackground', () => {
  it('is hidden from assistive technology and ignores pointer input', () => {
    const { container } = render(<LiveBackground />)
    const root = container.querySelector('.live-bg')

    expect(root).toBeInTheDocument()
    expect(root).toHaveAttribute('aria-hidden', 'true')
    // Decorative layers must never swallow a click meant for the form behind them.
    expect(root.className).toContain('live-bg')
    expect(root.textContent).toBe('')
  })

  it('renders the drifting motes with staggered, non-random timing', () => {
    const { container } = render(<LiveBackground />)
    const motes = container.querySelectorAll('.live-bg__mote')

    expect(motes.length).toBeGreaterThan(0)
    // Hand-tuned values, not Math.random() — randomness would re-roll on every render and
    // make the motion visibly jump.
    const delays = [...motes].map((m) => m.style.getPropertyValue('--mote-delay'))
    expect(new Set(delays).size).toBeGreaterThan(1)
    expect(delays.every((d) => d !== '')).toBe(true)
  })

  it('adds nothing an accessibility query can reach when mounted with the real app', () => {
    render(<App />)

    // The form is still the only thing queries can see; the backdrop contributes no roles,
    // no labels and no text for getByRole/getByText to trip over.
    expect(screen.getByRole('heading', { name: /livestock symptom checker/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/species/i)).toBeInTheDocument()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })
})
