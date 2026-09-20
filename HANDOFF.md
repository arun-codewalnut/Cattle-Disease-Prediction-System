# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-20)

- Confirmed M13's PR (#22) had already been merged to `main` — synced before branching for M14.
- **Implemented M14** (issue #23): Dog added as a fifth species. See STATE.md for the full
  detail list.
- **Central decision, confirmed with the user before coding, not assumed**: mirror M13's
  conservative "block diagnosis entirely, don't source data/train a model this session" call
  rather than issue #23's literal wording. Asked via `AskUserQuestion` (M13-style block vs.
  full scope with real dataset sourcing + training); the user picked the conservative option.
- Did real web research (AVMA, VCA, AKC) for the dog disease list required by issue #23 —
  canine distemper, canine parvovirus, kennel cough (CIRDC), sarcoptic/demodectic mange — and
  re-confirmed the same Hugging Face/Kaggle dataset candidates M13 found, still not downloaded.
- Reread `docs/DISCLAIMER.md` before touching it and found it already dog-inclusive from M13
  ("companion animals (cat, dog)", "cats and dogs") — made **no edit** to it this session,
  documented as a deliberate decision in the spec rather than silently skipping a step M13 did.
- Confirmed `DiagnosisIntake.jsx`/`AnimalIdentityFields.jsx` needed no code changes — both
  already gate generically on `DIAGNOSIS_SUPPORTED_SPECIES`, no Cat-specific hardcoding to
  generalize.
- **Validated, then committed**: backend 23/23, ml-service confirmed unaffected (no
  ml-service files touched), frontend lint + 12/12 + build, plus a live end-to-end run: `curl`
  confirmed a Dog animal's symptom and image diagnosis both reject with a clean `400
  DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`, a Cow diagnosis still succeeded normally, and a real
  browser run confirmed selecting Dog hides the diagnosis forms entirely (Cow still works after
  switching back).

## Next session

- Open a PR for M14 (issue #23) once the user confirms — not opened yet this session.
- M14 is the last of the five originally-requested species (`docs/ROADMAP.md`'s "Target
  species" note) — no more species milestones queued after this.
- **Real cat/dog models are still blocked on data** — candidates are known (Hugging Face
  `karenwky/pet-health-symptoms-dataset`, two Kaggle multi-species datasets) but nothing has
  been downloaded across M13 or M14. Worth asking the user directly: should a follow-up issue
  be opened to evaluate/download one of these?
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
  chat) and confirms it's there. Carried over six sessions now, still blocking.
- **M13/M14 found real cat/dog-disease dataset candidates but didn't fetch them** — not
  strictly a blocker (both shipped without needing them, by design), but real follow-up work
  needs the user's decision on which candidate (if any) to pursue, and possibly a Hugging Face
  token or a review of the Kaggle datasets' licensing.
- `GITHUB_TOKEN` used by the GitHub MCP server is invalid ("Bad credentials" on every MCP
  call, multiple sessions running now) — not blocking, since `gh` CLI has a separate working
  keyring login (`env -u GITHUB_TOKEN gh ...` per call), but MCP itself needs a real token
  refresh at some point instead of relying on that workaround indefinitely.
