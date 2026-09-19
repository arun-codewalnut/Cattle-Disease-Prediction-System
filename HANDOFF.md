# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-18)

- Confirmed M10's PR had already been merged to `main` — synced before branching for M11.
- **Implemented M11** (issue #20): Buffalo added as a second species. This was the
  architecturally significant one in the M11–M14 sequence — see STATE.md for the full
  detail list. Two decisions made and logged in `docs/DECISIONS.md` rather than deferred:
  1. Renamed `Cattle` → `Animal` throughout `backend` now, not later — 3 more species
     already planned (M12–M14), so doing this once now beats repeating the discussion.
  2. Buffalo reuses the cattle-trained model, explicitly disclosed — no buffalo dataset was
     found (researched via web search, not assumed), and unlike M1's synthetic tabular
     data, there's no honest fallback for a real model. Mirrors M8's "wire the pipeline,
     disclose the limitation" pattern.
- Used a research subagent to map every backend file touching `Cattle` before starting the
  rename, rather than discovering references reactively file-by-file — found the exact
  V1 migration SQL, the `DiagnosisCase.cattleId` FK column, and every test method name in
  one pass, which made the actual rename mechanical instead of exploratory.
- Proactively fixed a bug class before a user hit it this time: `GlobalExceptionHandler` now
  handles malformed JSON/invalid enum values cleanly, since M11's `species` field is the
  first thing that could actually trigger the same raw-exception-leak bug fixed reactively
  for blank `tagNumber` in the M8 PR.
- **Validated, then committed**: backend 17/17 (clean build, migration verified applying),
  ml-service unaffected (confirmed, not assumed — no ml-service files were touched),
  frontend lint + 9/9 + build, plus a live browser run creating a Buffalo animal and
  confirming both the disclosure and correct escalation. All M11 work committed (3 focused
  commits: backend rename, frontend, docs) — see git log on
  `feat/m11-buffalo-disease-detection`. PR opened against `main`.

## Next session

- Review and merge the issue #20 PR (M11) once it's had a look.
- M12 (Sheep, issue #21) can now reuse M11's species architecture directly — that spec
  should be much smaller than M11's, mostly about sheep-specific disease coverage/data, not
  another architecture discussion.
- **Still waiting on the user for M9's dataset** (issue #18 stays open, spec-only) — see
  Blockers.
- Decide on a `LICENSE` (still open, carried over from several sessions back).
- Fix `GITHUB_TOKEN` for GitHub MCP so the `gh` CLI workaround (`env -u GITHUB_TOKEN gh ...`)
  isn't needed every session.
- Other open issues, unstarted: M7 (notifications, #7), M13/M14 (Cat/Dog, #22/#23 — M13 is
  a bigger pivot to companion-animal diseases, flagged for its own `DISCLAIMER.md` review).
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
  three sessions now, still blocking. Same situation will likely recur for M12–M14's
  species-specific datasets — worth asking the user up front next time rather than
  rediscovering the same wall each milestone.
- `GITHUB_TOKEN` used by the GitHub MCP server is invalid ("Bad credentials" on every MCP
  call, multiple sessions running now) — not blocking, since `gh` CLI has a separate working
  keyring login (`env -u GITHUB_TOKEN gh ...` per call), but MCP itself needs a real token
  refresh at some point instead of relying on that workaround indefinitely.
