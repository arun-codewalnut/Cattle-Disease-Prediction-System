# Spec: Frontend UI redesign (cattle theme, responsive, icon-driven)

**Milestone**: none (tracked as issue #15, not a numbered roadmap milestone)
**Status**: in progress

## Actor + goal

A farmer/vet opens the symptom checker on a phone or laptop and can tell at a glance, without
reading dense text, what the app is for and what each control does — via a cattle/farm visual
theme, colorful cohesive styling, icons/emoji on fields and actions, and a results view that
communicates urgency visually as well as textually. The app must look and behave correctly
from narrow mobile widths up through desktop.

## Boundaries & failure states

- Purely presentational: no change to `DiagnosisIntake`'s state machine, the two-call
  create-cattle-then-submit-symptoms flow, the `X-Correlation-Id` generation, or the
  `{code, message, details}` error handling path from M4.
- No change to which DOM elements carry semantic roles/labels: every `<label htmlFor>`/`id`
  pairing, `<fieldset>`/`<legend>`, `role="alert"`, and `aria-live="polite"` stays exactly
  where it is today — only wrapping markup, classes, and visual styling change. Existing
  Vitest queries (`getByLabelText`, `getByRole`) must keep resolving to the same elements.
- Decorative additions (icons, emoji, background art) are marked `aria-hidden="true"` where
  they're not already implied by the text they sit next to, so they don't get read twice by
  screen readers or picked up by text-based test queries.
- All background/decorative imagery is either an emoji (Unicode, no license issue), inline
  hand-authored SVG/CSS (original, no license issue) — no downloaded stock photography, so
  there's no licensing risk.
- Color contrast: body text stays at or above WCAG AA contrast against its background in both
  the light and dark variants already defined in `index.css`.

## Examples

- **Mobile (< 480px)**: header stacks logo above title; symptom checkboxes render as a single
  column of tappable chip-style rows (large hit target); form width fills the viewport with a
  16px gutter.
- **Desktop (> 1024px)**: symptom checkboxes render as a multi-column grid; card is
  center-aligned with a max width, background is a full-bleed farm-toned gradient.
- **Input hover/focus**: hovering a text input lifts it slightly and darkens its border;
  focusing shows a visible accent-colored outline (keyboard-navigable, not just `:hover`).
- **Result — escalate_to_vet**: result card gets a red-toned left border/badge and a 🚨-style
  icon; existing text "Likely: Foot and Mouth Disease (81% confidence)" and "Escalate to vet"
  render unchanged, just inside the new visual treatment.
- **Result — monitor**: same card shape, green-toned accent instead of red.

## Not in scope

- Any backend or ml-service change.
- The image-upload disease-recognition feature (tracked separately as issue #16 / M8).
- A design-system/component-library dependency (e.g. MUI, Tailwind) — plain CSS matching the
  existing `index.css`/`App.css` convention, to keep the dependency footprint minimal (same
  reasoning M4 used for not adding a test-mocking library).
- Downloaded/stock photography of cattle — emoji + original CSS/SVG only, to avoid licensing
  and asset-pipeline complexity in a learning project.
- Animation libraries — CSS transitions only.

## Acceptance criteria

- [x] Spec written in `docs/specs/` before implementation (this file).
- [x] Intake and results screens render correctly at mobile (~375px), tablet (~768px), and
      desktop (~1280px) widths, verified in a real browser.
- [x] All form inputs (text, number, checkboxes, submit button) have a visible hover state and
      a visible, distinct focus state.
- [x] Background styling and icons use only emoji, inline SVG, or CSS — no external image
      assets.
- [x] Results view shows an urgency-coded visual treatment (icon + accent color) in addition
      to the existing text, for all three `recommendedAction` values.
- [x] Existing Vitest suite (`DiagnosisIntake.test.jsx`) passes unmodified — no test changes
      required because label text, roles, and structure are preserved.
- [x] `npm run build` and `npm run lint` succeed with no new errors.

## Agent mirror-back

**Intent**: restyle the existing M4 intake/result flow — same components, same state, same
API contract — with a cattle/farm visual identity, responsive layout, and icon-driven
affordances. This is a CSS/markup-wrapping pass, not a rewrite.

**Inputs/outputs**: unchanged (form inputs in, `DiagnosisResult` or an error message out).

**Assumptions flagged before coding**:
1. "Background image of cattle" is implemented as CSS gradient + emoji/inline-SVG motifs
   rather than a downloaded photo, per the "no stock photography" scoping decision above —
   flagged explicitly since the original request said "background image of cattle" and could
   have meant a literal photo.
2. Emoji are prefixed onto existing visible label text (e.g. "🤒 Fever") rather than replacing
   it, so `getByLabelText(/fever/i)`-style substring queries keep matching without any test
   changes.
3. The urgency icon/badge in `DiagnosisResult` is added as a sibling element to the existing
   `role="alert"` span, not inside it, so the alert's accessible text is unchanged.

## Follow-up: live (animated) background — 2026-09-22

The user asked for a "live background related to our application." This extends the spec
above rather than reversing it, and the reasoning is worth recording because the pull is
toward something much more literal.

**Atmospheric, not illustrative.** An earlier pass had already replaced illustrated farm
scenery with a calm accent-tinted gradient, on the grounds that this should read as "a calm,
professional tool, not a theme" (see the comment on `body` in `index.css`). That still holds:
the app tells a farmer their animal may have a **reportable disease**, and animated livestock
would undercut credibility at exactly the moment someone reads "escalate to vet." What moves
is therefore light and air over a field — three slow daylight washes, a horizon glow, and
drifting pollen — implemented in `LiveBackground.jsx` + the `.live-bg` rules in `App.css`.

**Boundaries this inherits from the spec above, unchanged:**
- Original CSS only — no animation library, no canvas, no downloaded imagery. ("Animation
  libraries" stays out of scope; CSS keyframes are the same no-dependency approach the
  "CSS transitions only" line already established.)
- Colors derive from existing tokens (via `color-mix` on the solid tokens, since the `*-bg`
  tokens sit at 0.10-0.12 alpha — tuned for a chip fill behind text, far too faint for a
  full-viewport wash), so dark mode flips for free.
- Decorative: `aria-hidden="true"`, `pointer-events: none`, no text, so no
  `getByRole`/`getByText`/`getByLabelText` query can reach into it.

**Added constraints specific to motion:**
- **`prefers-reduced-motion: reduce` disables it entirely** — the composition stays, the
  motion stops, and the motes are removed rather than frozen mid-air. Drifting peripheral
  motion is a genuine vestibular trigger, and this is a health-adjacent tool.
- **Only `transform`/`opacity` animate**, so everything composites on the GPU: no JS loop, no
  layout/paint thrash, nothing that drains a phone battery in a field.
- **Cycle lengths stay long** (34-92s). Anything quicker reads as fidgeting in peripheral
  vision while someone is reading a diagnosis.
- **Contrast is unaffected.** Body text sits on the opaque card; the header text sits on the
  washes, so it was checked against the worst case (both top glows overlapping at full
  strength): heading 9.51:1 and tagline 7.23:1 in light mode, 6.93:1 and 5.39:1 in dark — all
  above the AA 4.5:1 floor the spec already requires.

**Deliberately not done**: tinting the background by result urgency (red on escalate). The
result card already carries urgency; making the whole page react would read as alarming
theatre on a tool whose credibility depends on not overstating things.
