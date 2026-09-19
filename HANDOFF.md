# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-19)

- Confirmed M12's PR had already been merged to `main` — synced before branching for M13.
- **Implemented M13** (issue #22): Cat added as a fourth species — the real pivot in the
  M11–M14 sequence, as expected. See STATE.md for the full detail list.
- **The central judgment call this session: refused to reuse the cattle model for Cat.**
  M11/M12 reused it for Buffalo/Sheep because those species share the livestock disease
  family closely enough to call it a disclosed approximation. A cat doesn't get Foot and
  Mouth Disease or Lumpy Skin Disease, and the model's symptom vocabulary
  (`milk_yield_drop`, `udder_swelling`) doesn't even apply to a cat. Predicting a cattle
  disease name for someone's pet would be a real correctness/safety problem, not a scoping
  shortcut — so diagnosis is blocked entirely for Cat instead, enforced at both the backend
  (rejects even a direct API call) and frontend (no submittable form exists) layers. This
  was more conservative than issue #22's literal "train and wire in a cat-aware model"
  wording, and worth flagging clearly rather than quietly narrowing scope.
- Resolved the three open questions from issue #22 with real web research, not assumptions:
  a starter cat disease list (URI, ringworm, FIV), rabies as the confirmed
  legally-mandatory companion-animal escalation-equivalent, and a new companion-animal
  section in `docs/DISCLAIMER.md`.
- Found real candidate cat-disease datasets this time (a Hugging Face-mirrored symptom
  dataset, Roboflow image sets) — unlike the "nothing found" outcome for Buffalo/Sheep.
  Did not download anything — flagged for the user's decision, same "ask before fetching"
  boundary as M9's Kaggle situation.
- **Validated, then committed**: backend 21/21, ml-service confirmed unaffected, frontend
  lint + 11/11 + build, plus a live browser run confirming Cat hides the diagnosis forms
  entirely and a direct `curl` check confirming both diagnosis endpoints reject a Cat animal
  cleanly. All M13 work committed (3 focused commits: backend, frontend, docs) — see git log
  on `feat/m13-cat-disease-detection`. PR opened against `main`.

## Next session

- Review and merge the issue #22 PR (M13) once it's had a look.
- M14 (Dog, issue #23) should be lighter now that M13 settled the companion-animal framing —
  likely similar in shape to M13 itself (block diagnosis, document a disease list, reuse the
  rabies escalation-equivalent) rather than a new framing discussion, unless dog-specific
  research turns up a reason to diverge.
- **Real cat/dog models are still blocked on data** — but this time there are actual
  candidates worth evaluating (see STATE.md's M13 entry) rather than "nothing found." Worth
  asking the user directly: should a follow-up issue be opened to evaluate/download the
  Hugging Face pet-symptoms dataset or the Roboflow cat-skin/ringworm image sets?
- **Still waiting on the user for M9's cattle-image dataset** (issue #18 stays open,
  spec-only) — see Blockers.
- Decide on a `LICENSE` (still open, carried over from several sessions back).
- Fix `GITHUB_TOKEN` for GitHub MCP so the `gh` CLI workaround (`env -u GITHUB_TOKEN gh ...`)
  isn't needed every session.
- M7 (notifications, issue #7) is still open and unstarted, independent of the species work.
- `npx playwright install --with-deps chromium` in `tests/e2e/` — still not done.
- Consider a future cleanup pass: `docker-compose.yml`'s `chroma` service and
  `CHROMA_HOST`/`CHROMA_PORT` in `.env.example` are still unused (M6 uses embedded Chroma) —
  flagged, not urgent.

## Blockers

- **M9 needs a Kaggle account/API token to download the candidate cattle-image dataset**
  ([devang03mgr/cattle-diseases-datasets](https://www.kaggle.com/datasets/devang03mgr/cattle-diseases-datasets)) —
  the user hasn't provided one yet. Two ways to unblock: (a) the user downloads it manually
  and gives the local folder path, or (b) the user places a Kaggle API token at
  `~/.kaggle/kaggle.json` or via `KAGGLE_USERNAME`/`KAGGLE_KEY` env vars (never pasted in
  chat) and confirms it's there. Carried over five sessions now, still blocking.
- **M13 found real cat-disease dataset candidates but didn't fetch them** — not strictly a
  blocker (M13 shipped without needing them, by design), but real follow-up work needs the
  user's decision on which candidate (if any) to pursue, and possibly a Hugging Face token
  or Roboflow API key depending on which one.
- `GITHUB_TOKEN` used by the GitHub MCP server is invalid ("Bad credentials" on every MCP
  call, multiple sessions running now) — not blocking, since `gh` CLI has a separate working
  keyring login (`env -u GITHUB_TOKEN gh ...` per call), but MCP itself needs a real token
  refresh at some point instead of relying on that workaround indefinitely.
