# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-20, continued further still)

- PR #32 (real Cat/Dog image models) pushed, opened, and CI-green (`frontend`/`backend`/
  `ml-service` all pass; `mergemitra-analysis` fails the same way it did on #31 — an org-level
  check unrelated to this repo's own workflow, not something to chase). Not merged yet.
- Added a `README.md` section on testing diagnosis manually and retraining any model from
  scratch, plus fixed a duplicate `dog_image_model.pt` row in `REGISTRY.md` (the training
  script appends rather than replaces — caught this while pulling exact numbers to answer
  "how much data is each model trained on").
- You asked for a UI pass: a species preview image on selection, up to 5 photos per diagnosis
  with a warning if they disagree, and general visual polish. Showed a quick interactive
  mockup first to align on direction before building. Two real decisions surfaced and got your
  explicit answer rather than a guess:
  1. **What "5 photos disagree" means**: compare the 5 photos' own diagnosis results against
     each other, not verify "is this actually a cat" (no species-detection model exists — that
     would be new scope, flagged, not started).
  2. **Branching**: new branch `feat/multi-photo-diagnosis-ui`, stacked on the still-open
     Cat/Dog branch rather than waiting for #32 to merge, so it could use the working Cat/Dog
     image endpoints right away.
- **Implemented**: `POST /api/animals/{id}/diagnoses/image` now takes 1-5 files and returns
  `ImageDiagnosisBatchResponse { results, diagnosesAgree }` (breaking change, same
  no-versioning-ceremony precedent as M11) — backend loops the existing single-image
  `ml-service` call per photo, **no ml-service changes needed**. Frontend gained a 5-slot photo
  tray (`ImageUploadForm.jsx`, reworked), a species preview card that swaps instantly on
  selection (`SpeciesPreview.jsx`, new), a disagreement warning banner
  (`DiagnosisResult.jsx`, split into card + list), and general polish (animated spinner,
  entrance animations, kept the existing farm-themed background since it was already good).
- **Validated, not yet committed**: backend 16/16, frontend 14/14 + build. Live end-to-end via
  `curl`: disagreement correctly detected in two real cases (a misclassified Cat photo, an
  "uncertain" Dog photo mixed with two Mange photos), `TOO_MANY_IMAGES` correctly rejects a
  6th photo. Confirmed in the real browser (desktop + mobile) that the species preview swaps
  correctly and the photo tray's 5 slots have correct accessible labels — could not literally
  drive the file picker in the built-in browser (same limitation noted for M9's manual
  verification), covered instead by the passing Vitest `user.upload()` tests.

## Next session

- **Commit and (if asked) push/PR the multi-photo/UI work** — stopped after verification to
  hand off cleanly. This PR's diff will include PR #32's changes until #32 merges (it's
  stacked on that branch) — mention that in the new PR's description so it's not a surprise
  in review.
- Merge PR #32 (and then this new one, once opened) when ready.
- Buffalo/Sheep still have zero real data of any kind — unchanged by anything recent.
- Dog's image model quality (52.6% accuracy) is still a real, standing concern, now made more
  visible via the loud UI warning and the disagreement banner (a Dog photo batch will likely
  show disagreement often, by design — that's the model being honest about its own limits,
  not a UI bug).
- Decide on a `LICENSE` (still open, carried over from several sessions back).
- Fix `GITHUB_TOKEN` for GitHub MCP so the `gh` CLI workaround (`env -u GITHUB_TOKEN gh ...`)
  isn't needed every session.
- M7 (notifications, issue #7) is still open and unstarted, independent of everything above.
- `npx playwright install --with-deps chromium` in `tests/e2e/` — still not done.
- Consider a future cleanup pass: `docker-compose.yml`'s `chroma` service and
  `CHROMA_HOST`/`CHROMA_PORT` in `.env.example` are still unused (M6 uses embedded Chroma) —
  flagged, not urgent.
- Possible follow-up flagged during this session, not started: a real species-detection model
  (verify an uploaded photo actually looks like the selected species) — meaningfully bigger
  scope than what was built here, needs its own data-sourcing pass.

## Blockers

- **Buffalo/Sheep real model**: no image or symptom data found for either across any session
  so far — would need fresh dataset research if this becomes a priority.
- **Dog image model quality**: real data exists and was used, the result is just weak for 3 of
  4 classes. A different kind of data (photos where systemic symptoms are visually apparent
  rather than close-up skin shots) might help more than additional volume of the same kind;
  unverified, worth testing if picked up again.
- `GITHUB_TOKEN` used by the GitHub MCP server is invalid ("Bad credentials" on every MCP
  call, multiple sessions running now) — not blocking, since `gh` CLI has a separate working
  keyring login (`env -u GITHUB_TOKEN gh ...` per call), but MCP itself needs a real token
  refresh at some point instead of relying on that workaround indefinitely.
