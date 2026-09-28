# Spec: Two-screen diagnosis UI (Symptoms / Photo) with a split result view

**Milestone**: none (UI improvement, post-M16)
**Status**: done

## Actor + goal

A farmer, vet or pet owner opens the app and chooses **how** to get a diagnosis — from
**symptoms** or from **photos** — instead of scrolling one long page with both forms stacked
and separated by "or". While they fill in the form it sits centred; when they submit, the form
slides to the left and the result appears on the right, so the inputs and the answer are
visible side by side.

## Boundaries & failure states

- **Two screens, one toggle.** A `Symptoms | Photo` tab list at the top of the panel; each tab
  shows only its own form. Accessible as a real tab list (`role="tablist"`/`tab`/`tabpanel`,
  arrow keys move between tabs).
- **Species per screen.** Symptoms offers only species with a symptom model (Cow, Sheep,
  Goat); Photo offers all five. Switching to Symptoms while Cat or Dog is selected falls back
  to Cow. The one-line capability summary under the species select describes the current
  screen.
- **Layout states.**
  - *Idle*: the panel is centred, at a comfortable reading width.
  - *Submitting*: the panel slides left and a right-hand "Diagnosis result" region shows a
    loading state.
  - *Success*: the result (unchanged content and safety wording) fills the right-hand region;
    a **New diagnosis** button under it clears everything and re-centres the panel.
  - *Error*: the error message (`role="alert"`) appears in the right-hand region, where the
    result would have been.
- **What clears a shown result** (and re-centres the panel): switching tab, changing species,
  or pressing New diagnosis. Editing symptoms or photos keeps the split view so the user can
  adjust and resubmit.
- **Responsive.** Below 900px wide there's no room for two columns: the result appears below
  the form and the page scrolls to it. The transition is CSS-only and disabled under
  `prefers-reduced-motion`.
- **Unchanged**: the API calls, correlation IDs, error handling path, result card content
  (confidence wording, escalation, precautions, next steps, disclaimer, disagreement banner,
  invalid-image and wrong-species cards), and every existing label, legend and live region.
  Plain CSS, no new dependencies (same rule as docs/specs/frontend-ui-redesign.md).

## Examples

- Open app → Symptoms tab selected, species Cow, 11 cattle symptoms, panel centred, no result
  region.
- Tick Fever + Mouth lesions + Excessive salivation + Lameness → **Get diagnosis** → panel
  moves left, right side shows "Analysing symptoms…", then "Likely: Foot and Mouth Disease
  (…% confidence)" with Escalate to vet.
- Click **Photo** → result cleared, panel centred, species list now includes Cat and Dog.
- Photo tab, Cat, two photos → **Diagnose from photos** → two result cards on the right.
- Phone (375px): same flow, result stacked under the form.

## Not in scope

- Any backend or model change; any change to result wording or safety behaviour.
- A separate landing page (the toggle replaces it — agreed with the owner).
- Routing/URLs per screen.

## Acceptance criteria (must be checkable)

- [x] The page shows a Symptoms/Photo tab list; each tab shows only its own form.
- [x] The Symptoms species list has exactly Cow, Sheep, Goat; the Photo list has all five.
- [x] No result region exists before submitting; submitting shows it (loading, then result or
      error).
- [x] Switching tab, changing species, and New diagnosis each remove the result region.
- [x] Desktop: form left, result right. Below 900px: result below the form.
- [x] All existing frontend tests (adapted to the tabs) and new layout tests pass; lint and
      build pass; the e2e smoke test passes against the running stack.
- [x] Checked in a real browser at phone, tablet and desktop widths, light and dark mode.

## Agent mirror-back (fill before coding starts)

Restructure `DiagnosisIntake` into a mode toggle + one form per mode, and a two-column
workspace whose right column exists only once a submission starts. Keep the result card
component and every accessible name as they are. Owner-agreed defaults: toggle (not a landing
page), per-screen species lists, New diagnosis / tab / species change re-centre, errors shown
in the result area.

## Follow-up: visual emphasis (2026-09-28)

Owner request: a distinct page background, and the main items easy to pick out.

- Page background is a sage-green gradient (deep green in dark mode); form and result sit on
  white cards with a stronger shadow; the form card has a green accent strip on top.
- Result header is a solid bar in the urgency colour (red escalate / amber consult / green
  monitor) with white text — darkened in light mode so white text stays readable.
- The action block ("Escalate to vet" / "Consult a vet" / "Monitor") has a thick left bar and
  a larger heading in the urgency colour; "Meanwhile" has its own blue info treatment.
- The per-result "probabilistic estimate… always consult a vet" line was removed (owner's
  call); docs/DISCLAIMER.md records how the result still reads as an estimate.
