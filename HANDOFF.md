# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-20, continued)

- Pushed M14's branch and opened [PR #30](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/pull/30) against `main` — you merged it shortly after, confirmed before branching for M9.
- You gave `kagglehub`/`datasets` download snippets for all 4 previously-flagged candidate
  datasets and asked me to use them all. Downloaded and evaluated all 4 for real:
  - **Cattle images (`devang03mgr/cattle-diseases-datasets`)**: solid, real, 3,244 images —
    downloaded **anonymously, no Kaggle token needed** (the M9 spec's own "blocked, needs a
    Kaggle account" assumption turned out to be wrong).
  - **3 companion-animal datasets** (HF `pet-health-symptoms-dataset`, Kaggle
    `shijo96john/animal-disease-prediction`, Kaggle `gracehephzibahm/animal-disease`):
    inspected all 3 in detail — none good enough to train a trustworthy Cat/Dog model. Flagged
    this to you explicitly (`AskUserQuestion`) rather than silently training on thin data; you
    confirmed proceeding with the cattle image classifier only for now.
- **Implemented M9 for real** (issue #18): trained a MobileNetV2-transfer-learning cattle
  image classifier — 86.1% val accuracy / 0.857 macro F1 across `Healthy`/`Lumpy Skin
  Disease`/`Foot and Mouth Disease`. Replaced M8 phase 1's hash-based placeholder in
  `ml-service/app/agent/graph.py`'s `predict_image_node` with a real model call; removed the
  now-obsolete `image_placeholder` branch in `explain_node` so image diagnoses get real
  LLM/RAG explanations like symptom diagnoses do. See STATE.md for the full detail list.
- **Real architectural deviation, flagged deliberately**: the symptom model's tests retrain a
  fresh model every session from committed synthetic data (cheap, CI-safe) — the real image
  dataset can't follow that pattern (257MB, real photos, unverified redistribution license,
  so it's gitignored and CI won't have it). Real-model image tests skip gracefully via
  `@pytest.mark.skipif` when the local trained artifact is absent; a new test asserting the
  clean `MODEL_NOT_TRAINED` 503 always runs, since that's the actual behavior CI will see.
- **Validated, not yet committed**: ml-service 40 passed/2 skipped, backend 23/23 unaffected,
  frontend unaffected (no files touched in either service — species was never threaded to the
  image endpoint and still isn't). Live end-to-end: called both the real `ml-service`
  `/agent/diagnose` and the real backend `POST /api/animals/{id}/diagnoses/image` with one
  real photo per class — all 3 correctly diagnosed with correct escalation. **Could not**
  verify through the actual browser `<input type=file>` control — the built-in Browser pane
  has no file-upload tool — so browser verification stopped at the API layer, not the literal
  click-and-upload UI interaction; flagged rather than silently skipped.

## Next session

- **Commit and (if asked) push/PR the M9 work** — not done yet this session, stopped after
  verification to hand off cleanly. Suggested split: data+deps, model+training script, graph
  wiring, docs+tests (mirrors how M13/M14 split their commits).
- Companion-animal (Cat/Dog) real model: still blocked on data, now with **evaluated, not just
  found** candidates — worth discussing whether to look for a better/larger canine or feline-
  specific dataset (search terms used so far: generic "animal disease/symptom dataset" —
  a more targeted search might turn up something with better per-species sample counts).
- `requirements.txt` now pins `torch==2.14.0`/`torchvision==0.29.0` without the
  `--index-url https://download.pytorch.org/whl/cpu` flag baked in (pip doesn't support an
  index URL inside requirements.txt per-package) — CI's plain `pip install -r requirements.txt`
  may pull a much larger CUDA-enabled wheel instead of the CPU one used locally. Worth
  checking CI logs/timing once this is pushed; if it's a problem, a `constraints.txt` or a
  CI-specific install step pointing at the CPU index is the fix.
- Decide on a `LICENSE` (still open, carried over from several sessions back).
- Fix `GITHUB_TOKEN` for GitHub MCP so the `gh` CLI workaround (`env -u GITHUB_TOKEN gh ...`)
  isn't needed every session.
- M7 (notifications, issue #7) is still open and unstarted, independent of everything above.
- `npx playwright install --with-deps chromium` in `tests/e2e/` — still not done.
- Consider a future cleanup pass: `docker-compose.yml`'s `chroma` service and
  `CHROMA_HOST`/`CHROMA_PORT` in `.env.example` are still unused (M6 uses embedded Chroma) —
  flagged, not urgent.

## Blockers

- **Companion-animal (Cat/Dog) real model**: no longer "no data found" — now "data found,
  downloaded, evaluated, still insufficient." The best candidate (Kaggle
  `shijo96john/animal-disease-prediction`) has the right shape (species + structured symptoms
  + real disease names matching M13/M14's researched disease lists) but only ~75 Dog / ~72
  Cat rows spread across 20+ near-duplicate disease labels — needs either a bigger dataset or
  an explicit decision to ship something low-confidence with real, prominent caveats.
- `GITHUB_TOKEN` used by the GitHub MCP server is invalid ("Bad credentials" on every MCP
  call, multiple sessions running now) — not blocking, since `gh` CLI has a separate working
  keyring login (`env -u GITHUB_TOKEN gh ...` per call), but MCP itself needs a real token
  refresh at some point instead of relying on that workaround indefinitely.
