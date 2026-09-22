// Ambient, living backdrop — deliberately atmospheric rather than illustrative.
//
// The previous redesign settled on "a calm, professional tool, not a theme" (see the comment
// on `body` in index.css, and docs/specs/frontend-ui-redesign.md). That constraint still
// holds: this app tells a farmer their animal may have a reportable disease, so the backdrop
// has to stay credible. What moves here is light and air over a field — drifting daylight, a
// horizon glow, and a little pollen — never livestock, never anything fast enough to pull the
// eye away from a diagnosis someone is reading.
//
// Built to the same rules as the rest of the theme: original CSS only (no libraries, no
// downloaded imagery), colors from the existing tokens so it flips for dark mode for free,
// and only `transform`/`opacity` animated so it composites on the GPU — no JS loop, no
// canvas, nothing that drains a phone battery out in a field. Fully disabled under
// `prefers-reduced-motion`.
//
// Decorative only: aria-hidden, pointer-events: none, and no text, so screen readers skip it
// and no existing getByRole/getByText/getByLabelText query can match inside it.

// Hand-tuned rather than random: a Math.random() here would re-roll on every render and make
// the motion jump whenever React re-renders the tree.
const MOTES = [
  { left: 6, size: 4, delay: 0, duration: 34, drift: 14 },
  { left: 14, size: 6, delay: 7, duration: 44, drift: -10 },
  { left: 23, size: 3, delay: 15, duration: 38, drift: 18 },
  { left: 31, size: 5, delay: 3, duration: 50, drift: -16 },
  { left: 40, size: 4, delay: 21, duration: 41, drift: 9 },
  { left: 48, size: 7, delay: 11, duration: 55, drift: -12 },
  { left: 56, size: 3, delay: 27, duration: 36, drift: 15 },
  { left: 64, size: 5, delay: 5, duration: 47, drift: -8 },
  { left: 72, size: 4, delay: 18, duration: 52, drift: 12 },
  { left: 80, size: 6, delay: 9, duration: 39, drift: -14 },
  { left: 88, size: 3, delay: 24, duration: 45, drift: 10 },
  { left: 95, size: 5, delay: 13, duration: 58, drift: -11 },
]

export default function LiveBackground() {
  return (
    <div className="live-bg" aria-hidden="true">
      <div className="live-bg__glow live-bg__glow--sun" />
      <div className="live-bg__glow live-bg__glow--sky" />
      <div className="live-bg__glow live-bg__glow--field" />
      <div className="live-bg__horizon" />
      <div className="live-bg__motes">
        {MOTES.map((mote, index) => (
          <span
            key={index}
            className="live-bg__mote"
            style={{
              '--mote-left': `${mote.left}%`,
              '--mote-size': `${mote.size}px`,
              '--mote-delay': `-${mote.delay}s`,
              '--mote-duration': `${mote.duration}s`,
              '--mote-drift': `${mote.drift}vw`,
            }}
          />
        ))}
      </div>
    </div>
  )
}
