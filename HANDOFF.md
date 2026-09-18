# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-18)

- Confirmed M9's PR had already been merged to `main` (spec-only, per its own scope) —
  synced before starting new work.
- **Implemented M10** (issue #19): every diagnosis now returns `precautions`/`next_steps`.
  Key design call: this content is looked up verbatim from hand-authored reference docs via
  an exact `(disease, section)` match, **never LLM-generated** — treatment-adjacent guidance
  is too high-stakes to leave to a prompt, and a static, reviewed string can't drift the way
  LLM output could. See STATE.md for the full implementation detail list.
- Extended the RAG ingest pipeline to tag chunks by section (`overview` vs `precautions` vs
  `next-steps`) and restricted `retrieve()` (used for the LLM-grounded `explanation`) to
  `overview` only, so the two kinds of content can never mix in the explanation prompt —
  caught this as a design risk before writing any code, not after.
- **Validated three ways**, not just one: native pytest (RAG-independent tests), Docker
  pytest with real chromadb (the RAG-dependent tests, including a dedicated
  reportable-disease escalation-wording test), and a full live browser run against the real
  stack (ml-service in Docker with the re-ingested collection + native backend/frontend).
  Chased down one apparent bug (a mangled em-dash) far enough to confirm it was a false
  alarm — my own verification command's console encoding, not the app — before moving on,
  rather than either ignoring it or "fixing" something that wasn't broken.
- All M10 work committed (4 focused commits: ml-service, backend, frontend, docs) — see git
  log on `feat/m10-precautions-next-steps`. PR opened against `main`.

## Next session

- Review and merge the issue #19 PR (M10) once it's had a look.
- **Waiting on the user for M9's dataset** (issue #18 stays open, spec-only so far) — see
  Blockers. Once available: `ml-service/training/image_model_train.py`, train, record real
  evaluation metrics in `ml-service/models/REGISTRY.md`, wire into `predict_image_node`,
  remove the M8 `image_placeholder` explain-path branch (M10's `add_precautions` node
  already runs for the placeholder path too, so precautions/next-steps will keep working
  once the real model lands — nothing to redo there), update
  `docs/API_CONTRACTS.md`/`DISCLAIMER.md` for 3-class (not 5-class) image coverage.
- Decide on a `LICENSE` (still open, carried over from several sessions back).
- Fix `GITHUB_TOKEN` for GitHub MCP so the `gh` CLI workaround (`env -u GITHUB_TOKEN gh ...`)
  isn't needed every session.
- Other open issues, unstarted: M7 (notifications, #7), M11–M14 (Buffalo/Sheep/Cat/Dog,
  #20–#23).
- `npx playwright install --with-deps chromium` in `tests/e2e/` — still not done.
- Consider a future cleanup pass: `docker-compose.yml`'s `chroma` service and
  `CHROMA_HOST`/`CHROMA_PORT` in `.env.example` are still unused (M6 uses embedded Chroma) —
  flagged, not urgent.

## Blockers

- **M9 needs a Kaggle account/API token to download the candidate dataset**
  ([devang03mgr/cattle-diseases-datasets](https://www.kaggle.com/datasets/devang03mgr/cattle-diseases-datasets)) —
  the user hasn't provided one yet. Two ways to unblock: (a) the user downloads it manually
  and gives the local folder path, or (b) the user places a Kaggle API token at
  `~/.kaggle/kaggle.json` or via `KAGGLE_USERNAME`/`KAGGLE_KEY` env vars (never pasted in
  chat) and confirms it's there, so the `kaggle` CLI can be scripted directly. Carried over
  two sessions now, still blocking.
- `GITHUB_TOKEN` used by the GitHub MCP server is invalid ("Bad credentials" on every MCP
  call, multiple sessions running now) — not blocking, since `gh` CLI has a separate working
  keyring login (`env -u GITHUB_TOKEN gh ...` per call), but MCP itself needs a real token
  refresh at some point instead of relying on that workaround indefinitely.
