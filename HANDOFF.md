# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-18)

- Listed all open issues on request — noted issue #16 (M8 phase 1) had already been closed,
  because **PR #24 was merged directly on GitHub** (outside this session) — synced local
  `main` before doing anything else.
- **Started M9** (issue #18): created branch `feat/m9-cattle-image-classifier` from synced
  `main`, re-validated the full baseline first (ml-service 29/2, backend 15/15, frontend
  7/7 + lint + build — all green, confirming a clean starting point), then wrote the spec.
- **Hit the same blocker M1 hit, but this time it can't be worked around the same way**: no
  Kaggle account/API token in this environment to download the candidate dataset, and unlike
  M1's synthetic-tabular fallback, there's no honest synthetic fallback for an *image*
  classifier — fake images would teach a CNN nothing real about actual cattle diseases.
  Stopped at "spec written," flagged the blocker clearly, and asked the user for either the
  downloaded dataset's local path or a Kaggle API token placed where the `kaggle` CLI expects
  it (not pasted in chat). Spec:
  [docs/specs/M9-cattle-image-classifier.md](docs/specs/M9-cattle-image-classifier.md).
- Committed the spec + STATE.md/HANDOFF.md updates and opened a PR against `main` — even
  though there's no implementation yet, per this repo's spec-first convention the spec itself
  is a real, reviewable deliverable ("spec written and agreed" is issue #18's first
  acceptance criterion).

## Next session

- **Waiting on the user for M9's dataset** — see Blockers. Once available: build
  `ml-service/training/image_model_train.py`, train, record real evaluation metrics in
  `ml-service/models/REGISTRY.md`, wire into `predict_image_node`, remove the M8
  `image_placeholder` explain-path branch, update `docs/API_CONTRACTS.md`/`DISCLAIMER.md`
  for 3-class (not 5-class) image coverage.
- Review and merge the issue #18 PR (M9 spec) once it's had a look.
- Decide on a `LICENSE` (still open, carried over from several sessions back).
- Fix `GITHUB_TOKEN` for GitHub MCP so the `gh` CLI workaround (`env -u GITHUB_TOKEN gh ...`)
  isn't needed every session.
- Other open issues, unstarted: M7 (notifications, #7), M10 (precautions/next-steps, #19),
  M11–M14 (Buffalo/Sheep/Cat/Dog, #20–#23).
- `npx playwright install --with-deps chromium` in `tests/e2e/` — still not done.
- **ml-service tests touching RAG still need Docker** (unchanged from prior sessions) — see
  `ml-service/AGENTS.md` for the build/test command.
- Consider a future cleanup pass: `docker-compose.yml`'s `chroma` service and
  `CHROMA_HOST`/`CHROMA_PORT` in `.env.example` are still unused (M6 uses embedded Chroma) —
  flagged, not urgent.

## Blockers

- **M9 needs a Kaggle account/API token to download the candidate dataset**
  ([devang03mgr/cattle-diseases-datasets](https://www.kaggle.com/datasets/devang03mgr/cattle-diseases-datasets)) —
  the user hasn't provided one yet. Two ways to unblock: (a) the user downloads it manually
  and gives the local folder path, or (b) the user places a Kaggle API token at
  `~/.kaggle/kaggle.json` or via `KAGGLE_USERNAME`/`KAGGLE_KEY` env vars (never pasted in
  chat) and confirms it's there, so the `kaggle` CLI can be scripted directly. Nothing in
  `ml-service/training/` can be written or tested without real data — carried over from last
  session, still blocking.
- `GITHUB_TOKEN` used by the GitHub MCP server is invalid ("Bad credentials" on every MCP
  call, multiple sessions running now) — not blocking, since `gh` CLI has a separate working
  keyring login (`env -u GITHUB_TOKEN gh ...` per call), but MCP itself needs a real token
  refresh at some point instead of relying on that workaround indefinitely.
