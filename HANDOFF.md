# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-20, continued further)

- M9's PR ([#31](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/pull/31))
  hit a real CI failure after merge-adjacent testing looked clean locally: `pip install -r
  requirements.txt` on the Linux runner resolved `torch`/`torchvision` to PyPI's default CUDA
  build (hundreds of MB of `nvidia-*`/`triton` packages), exhausting the runner's disk. Fixed
  by pinning the `+cpu` version suffix and an `--extra-index-url` directive in
  `requirements.txt` — verified the fix in a disposable local venv against a plain `pip
  install -r requirements.txt` (no special flags) before pushing, matching exactly what CI
  runs. CI went green; the PR merged.
- You asked to train all 5 species so an uploaded photo gets a real diagnosis for each.
  Investigated honestly rather than assuming this was achievable: Buffalo/Sheep have zero
  image (or even symptom) data anywhere found across any session; Cat/Dog's best-known
  candidates (Roboflow, flagged back in M13) turned out to require a login/API key — confirmed
  by testing, not assumed. A fresh Kaggle search found real, adequate, anonymously-downloadable
  data for Cat and Dog specifically (not Buffalo/Sheep — still nothing there).
- **Trained and shipped real Cat and Dog image models** (branch
  `feat/m13-m14-real-cat-dog-image-models`, off synced `main` after M9 merged):
  - Cat: 83.0% accuracy, 0.829 macro F1 (Flea Allergy/Healthy/Ringworm/Scabies) — solid,
    comparable to M9's cattle model. Disease list changed from M13's original URI/Ringworm/FIV
    research since no image data exists for URI/FIV — confirmed with you before proceeding.
  - Dog: 52.6% accuracy, 0.489 macro F1 — genuinely weak, especially Canine Distemper (0.25
    F1). Tried a legitimate fix (flip augmentation, split before augmenting to avoid leaking
    into validation) — didn't help; likely a signal problem (systemic diseases lack a strong
    single-photo visual signature), not fixable with more of the same data. No Healthy class
    exists for Dog at all. **Confirmed with you explicitly**: ship it anyway, loudly disclosed
    (frontend warning + `docs/DISCLAIMER.md`), rather than withholding or quietly narrowing
    scope.
  - Real architecture change: species is now forwarded backend→ml-service for the **image**
    endpoint only (symptom path unchanged, still species-blind). `ml-service`'s
    `predict_image_node` picks the model by species, falling back to the cattle model for
    Cow/Buffalo/Sheep/unset — verified as a regression test, not just assumed unaffected.
  - Frontend's diagnosis-availability UI went from binary (full/blocked) to 3-way (full /
    image-only / blocked) — Cat/Dog now show only the photo upload form, each with its own
    disclosure (Cat: informational note; Dog: a loud ⚠️ warning with the real accuracy number
    and the no-Healthy-class gap, shown before any photo is even uploaded).
  - Rabies escalation is still not code — neither model has a Rabies class to attach the rule
    to. Not a gap introduced this session; the same honest "not yet" from M13, unchanged.
- **Validated, not yet committed**: ml-service 45/2 skipped (new Cat/Dog tests use random,
  seeded multi-image sampling after an initial single-sample version turned out flaky against
  a real, correctly-behaving-but-imperfect model), backend 24/24, frontend lint + 13/13 +
  build. Live end-to-end: real Cat/Dog photos through the actual backend multipart endpoint,
  correct diagnoses; confirmed symptom submission still rejects for both; confirmed Cow
  regression-free; confirmed in the real browser that Cat/Dog show the correct image-only UI
  with the right disclosure text.

## Next session

- **Commit and (if asked) push/PR the Cat/Dog work** — stopped after verification to hand off
  cleanly, same pattern as M9.
- Buffalo/Sheep still have zero real data of any kind (image or symptom) — still using the
  disclosed cattle-model approximation, unchanged by anything this session did. Worth another
  look if a future session wants to close that gap.
- Dog's image model quality is a real, standing concern — if better data ever turns up
  (specifically photos of *systemic* disease presentation, not just more skin-condition
  photos), worth revisiting; the current 52.6% accuracy is disclosed, not fixed.
- `requirements.txt`'s CPU-wheel pin is now confirmed working on real CI (not just locally) —
  no further action needed there unless torch/torchvision get upgraded again.
- Decide on a `LICENSE` (still open, carried over from several sessions back).
- Fix `GITHUB_TOKEN` for GitHub MCP so the `gh` CLI workaround (`env -u GITHUB_TOKEN gh ...`)
  isn't needed every session.
- M7 (notifications, issue #7) is still open and unstarted, independent of everything above.
- `npx playwright install --with-deps chromium` in `tests/e2e/` — still not done.
- Consider a future cleanup pass: `docker-compose.yml`'s `chroma` service and
  `CHROMA_HOST`/`CHROMA_PORT` in `.env.example` are still unused (M6 uses embedded Chroma) —
  flagged, not urgent.

## Blockers

- **Buffalo/Sheep real model**: no image or symptom data found for either across any session
  so far — would need fresh dataset research if this becomes a priority.
- **Dog image model quality**: not a "missing data" blocker in the usual sense — real data
  exists and was used, the result is just weak for 3 of 4 classes. A different kind of data
  (photos where the systemic symptoms are visually apparent — e.g., lethargy/nasal discharge
  framing rather than close-up skin shots) might help more than additional volume of the same
  kind; unverified, worth testing if picked up again.
- `GITHUB_TOKEN` used by the GitHub MCP server is invalid ("Bad credentials" on every MCP
  call, multiple sessions running now) — not blocking, since `gh` CLI has a separate working
  keyring login (`env -u GITHUB_TOKEN gh ...` per call), but MCP itself needs a real token
  refresh at some point instead of relying on that workaround indefinitely.
