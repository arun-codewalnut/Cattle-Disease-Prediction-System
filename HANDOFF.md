# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-22)

- Picked up on the `docs/readme-comprehensive-guide` branch's README work from a prior
  session, then moved into a UI redesign pass on the frontend: iterated through several
  directions for the species-selection panel (a real Wikimedia photo, 3D flip/tilt motion,
  a real drag-to-rotate `<model-viewer>` 3D model with smoothed normals) before you said you
  didn't like any of the motion/imagery approaches — reverted all of it, and the species
  panel is now **removed entirely**. The app is back to a single centered form (no
  photo/model panel), with a species capability summary shown as a plain inline caption
  under the species `<select>` instead. Background/typography also got a full pass: replaced
  the illustrated farm-theme background with a clean accent-tinted gradient (and fixed a
  real bug where the old background's hill illustration used hardcoded light-mode colors
  even in dark mode), tightened the whole typographic scale, and fixed a real pre-existing
  spacing bug (the species/tag-number/farm-ID fields had zero margin between them — a CSS
  selector, `form > div`, never matched them since those fields sit outside the `<form>`
  elements).
- **You asked "which species are trained well," then "is there any other species dataset
  available," then explicitly asked to remove Buffalo entirely and train Sheep with a real
  dataset found during that research.** Confirmed clear on scope via `AskUserQuestion`
  before touching anything (3 real judgment calls: Sheep's model should fully replace the
  cow-model approximation rather than fall back to it, Sheep's *image* path should keep
  using the cow model as an approximation since no sheep image dataset exists either way,
  and the M11 spec should be marked superseded rather than deleted).
- **Buffalo removed** across all three services: `Species` enum (backend), `SPECIES_OPTIONS`
  (frontend), new Flyway migration (`V3__remove_buffalo_species.sql`) cleaning up any
  existing `species = 'BUFFALO'` rows (the column has no DB-level enum/CHECK constraint —
  plain `VARCHAR(20)`, enforced only at the Java/JPA level, so no `ALTER TYPE` needed).
  `docs/specs/M11-buffalo-disease-detection.md` marked superseded (not deleted, per this
  repo's own "don't rewrite history" convention).
- **Sheep got a real, trained model**: found
  [PPR disease data from goats and sheep](https://www.kaggle.com/datasets/devothanyambo/ppr-disease-data-from-goats-and-sheep)
  on Kaggle — real field-collected clinical data (Tanzania, RT-qPCR-confirmed ground truth),
  downloadable anonymously via `kagglehub`. Built `app/models/sheep_symptom_model.py` (a
  6-feature binary XGBoost classifier — same architecture pattern as the cattle symptom
  model) and `training/sheep_symptom_model_train.py`; trained it — **80.5% CV accuracy,
  78.8% macro F1**, genuinely comparable to Cat's real model, not a weak result. One real
  data-quality finding, disclosed rather than papered over: the dataset's `animal` (species)
  column is pre-encoded to 0/1 with no data dictionary anywhere confirming which value means
  goat vs. sheep — so the model trains on the **combined goat+sheep file**, not a guessed-at
  "sheep-only" subset (PPR is the same disease in both, which is why the original study
  grouped them). Full writeup: `ml-service/data/sheep-symptoms/SOURCE.md`.
- **Wired end to end**: `species` is now forwarded to `ml-service` on the *symptom* path too
  (it wasn't before — only the image path was species-aware). `ml-service/app/agent/graph.py`
  gained `_SYMPTOM_MODEL_BY_SPECIES` (mirrors the existing `_IMAGE_MODEL_BY_SPECIES` pattern)
  routing `SHEEP` to the new model, everything else to the cattle model unchanged.
  `PPR (Peste des Petits Ruminants)` added to `REPORTABLE_DISEASES` (it's WOAH/OIE-notifiable,
  same escalation tier as FMD/LSD). Frontend: `symptomFields.js` now exports
  `getSymptomFields(species)` instead of one fixed list — Sheep renders its own 6-checkbox
  form (temp/nasal discharge/diarrhea/difficult breathing/eye discharge/oral-nasal lesions),
  completely different from cattle's vocabulary; switching species resets the symptom state
  to that species' own empty shape. Disclosure copy rewritten to describe the model's real,
  narrow scope (PPR only — "a negative result means 'not PPR,' not 'healthy'"), replacing the
  old "reusing the cow model as an approximation" wording for Sheep specifically.
- Docs updated to match: `docs/API_CONTRACTS.md`, `docs/DECISIONS.md` (new dated entry),
  `docs/ROADMAP.md`, `STATE.md`, `docs/specs/M12-sheep-disease-detection.md` (new "Follow-up"
  section) — plus this file.
- **Validated thoroughly**: backend 29/29 (Flyway migration applies cleanly against a real
  local Postgres), ml-service 50/2 (skipped — the usual RAG/chromadb local blocker, unrelated;
  7 new tests: 5 for the sheep model directly, 2 for graph.py routing), frontend lint clean +
  13/13 + build green. **Then live end-to-end against the real running stack** (not just
  mocks): started `ml-service` and `backend` fresh, created a real Sheep animal via the API,
  submitted real PPR-positive symptoms straight through the actual browser form, got back a
  correctly-diagnosed and correctly-escalated result; confirmed Buffalo is now rejected
  (`400 INVALID_REQUEST_BODY`) at the API level; confirmed Cow's symptom path is
  regression-free.
- **Image-mismatch/invalid-photo detection (M15), same session**: you described the intended
  UX directly — a clear photo gets a confident diagnosis, a real-but-unclear photo prompts
  for a clearer one, a completely unrelated photo (car/table) says the image is invalid.
  Confirmed via `AskUserQuestion` that the middle tier means "real animal, low confidence" —
  not "wrong species," which would need real per-species verification (bigger, separate,
  already-deferred scope). Built `app/models/species_gate.py`: a free, pretrained (zero
  fine-tuning) torchvision ImageNet-1k classifier gates every image-diagnosis path (all 4
  species, one shared implementation) before any disease model runs — a photo whose top-5
  predictions are all outside the verified animal-class index range (0–397) comes back
  `diagnosis: "invalid_image"` / `recommendedAction: "retry_upload"` instead of a fake
  disease guess. Tested against real data first: this repo's own cattle/cat/dog photos all
  pass, two real Wikimedia photos (table, car) both correctly rejected. **Real finding**:
  synthetic test images (solid color, noise) all incorrectly pass the gate — ~40% of
  ImageNet-1k classes are animals, so a degenerate image's top-5 has good odds of including
  one by chance; fine for the actual product problem (real accidental mismatched uploads),
  documented as a known limitation rather than hidden. Also fixed a real pre-existing bug
  found along the way: the `"uncertain"` explanation always said "not enough *symptom*
  information," even for a photo submission with no symptoms at all. Frontend gives
  `invalid_image` its own dedicated card (no fake confidence %, no vet-action badge); backend
  excludes it from the multi-photo `diagnosesAgree` comparison. Spec:
  `docs/specs/M15-image-diagnosis-quality-gate.md`. **Validated**: backend 33/33, ml-service
  63/2 (skipped, same RAG blocker), frontend lint + 14/14 green, **plus live verification
  against the real running stack**: a real car photo through the actual backend + ml-service
  came back correctly rejected; a real cat photo submitted right after still diagnosed
  correctly (regression-checked, same code path).

## Next session

- **Nothing has been committed or pushed yet** — all of the above (UI redesign, Buffalo
  removal, Sheep model, M15 image quality gate) is sitting in the working tree. Ask before
  committing/pushing, per the established per-action-permission pattern this repo's sessions
  have followed.
- `ml-service` and `backend` were left **running in the background** for the live
  verification above (ml-service on `:8000`, backend on `:8080`, against the existing
  `cattlecare-postgres` Docker container) — stop them if you don't need the stack up, or
  just restart fresh next session.
- A few real, throwaway test rows now exist in the local dev Postgres (`SHE-TEST-001`,
  `SHE-UI-001` tag numbers) from the live verification above — harmless, same as the
  `COW-001`-style test data already scattered through prior sessions' verification, not
  worth a cleanup pass on its own.
- Sheep's real gap is now narrower but not gone: the PPR model doesn't cover foot rot or
  sheep pox (flagged back in M12's original spec) — still true, unaffected by this session.
  If a sheep-specific *image* dataset ever turns up, that's the next real gap to close (photo
  diagnosis for Sheep still falls back to the cow image model).
- Decide on a `LICENSE` (still open, carried over from several sessions back).
- Fix `GITHUB_TOKEN` for GitHub MCP so the `gh` CLI workaround (`env -u GITHUB_TOKEN gh ...`)
  isn't needed every session.
- M7 (notifications, issue #7) is still open and unstarted, independent of everything above.
- `npx playwright install --with-deps chromium` in `tests/e2e/` — still not done.
- Consider a future cleanup pass: `docker-compose.yml`'s `chroma` service and
  `CHROMA_HOST`/`CHROMA_PORT` in `.env.example` are still unused (M6 uses embedded Chroma) —
  flagged, not urgent.
- `STATE.md`'s "In Progress"/older session entries drifted out of date before this session
  started (referenced work that had already actually been merged) — worth a proper audit
  pass at some point, not done here beyond what this session's own entry needed.

## Blockers

- **Dog image model quality**: real data exists and was used, the result is just weak for 3
  of 4 classes (52.6% accuracy overall). A different kind of data (photos where systemic
  symptoms are visually apparent rather than close-up skin shots) might help more than
  additional volume of the same kind; unverified, worth testing if picked up again.
- **Sheep's remaining disease gap**: foot rot and sheep pox still aren't represented by
  anything (the new PPR model is real but single-disease) — would need its own dataset
  search if this becomes a priority.
- `GITHUB_TOKEN` used by the GitHub MCP server is invalid ("Bad credentials" on every MCP
  call, multiple sessions running now) — not blocking, since `gh` CLI has a separate working
  keyring login (`env -u GITHUB_TOKEN gh ...` per call), but MCP itself needs a real token
  refresh at some point instead of relying on that workaround indefinitely.
