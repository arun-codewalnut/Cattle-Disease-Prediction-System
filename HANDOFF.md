# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-19)

- Confirmed M11's PR had already been merged to `main` — synced before branching for M12.
- **Implemented M12** (issue #21): Sheep added as a third species. Confirmed the M11
  architecture prediction was right — this needed no architecture change, just an enum
  value, a dropdown option, and updated copy. See STATE.md for the full detail list.
- The one thing worth carrying forward: **Sheep's gap is bigger than Buffalo's**. Buffalo's
  diseases (FMD, LSD) were at least a reasonable overlap with the existing 5-class model.
  Sheep's most common species-specific disease — foot rot — isn't represented by the model
  *at all*, and neither is sheep pox. Reused the Buffalo-era disclosure wording as a
  starting point but strengthened it rather than copy-pasting it unchanged, since "not
  trained on this species" would have undersold the real gap for Sheep specifically.
- **Validated, then committed**: backend 18/18, ml-service confirmed unaffected (no
  ml-service files touched), frontend lint + 10/10 + build, plus a live browser run creating
  a Sheep animal and confirming both the strengthened disclosure and correct escalation. All
  M12 work committed (3 focused commits: backend, frontend, docs) — see git log on
  `feat/m12-sheep-disease-detection`. PR opened against `main`.

## Next session

- Review and merge the issue #21 PR (M12) once it's had a look.
- M13 (Cat, issue #22) is the next real pivot — companion-animal diseases share almost
  nothing with the livestock disease list, so this one needs its own disease research and a
  `docs/DISCLAIMER.md` review (different audience: pet owner, not farmer/vet), not just
  another one-line species addition like M12 was.
- **Still waiting on the user for M9's dataset** (issue #18 stays open, spec-only) — see
  Blockers. Worth asking up front whether the user has (or wants to source) datasets for
  M13/M14 too, rather than rediscovering the same "no dataset found" wall a third time.
- Decide on a `LICENSE` (still open, carried over from several sessions back).
- Fix `GITHUB_TOKEN` for GitHub MCP so the `gh` CLI workaround (`env -u GITHUB_TOKEN gh ...`)
  isn't needed every session.
- M7 (notifications, issue #7) is still open and unstarted, independent of the species work.
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
  four sessions now, still blocking. Same "no dataset found" wall was hit again for M12
  (Sheep) — worth raising with the user proactively for M13/M14 rather than waiting to hit
  it a third and fourth time.
- `GITHUB_TOKEN` used by the GitHub MCP server is invalid ("Bad credentials" on every MCP
  call, multiple sessions running now) — not blocking, since `gh` CLI has a separate working
  keyring login (`env -u GITHUB_TOKEN gh ...` per call), but MCP itself needs a real token
  refresh at some point instead of relying on that workaround indefinitely.
