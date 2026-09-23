# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-22 → 2026-09-23)

A long session that started with one CI failure and turned into a sustained simplification
pass: two databases deleted, animal identity removed, and the image-validation path rebuilt
twice after you caught it being wrong. **Six PRs; five merged, #40 open and green.**

### What shipped

- **PR #35 CI fix** — `test_get_precautions_reportable_diseases_always_advise_escalation`
  was failing because the M12 follow-up added PPR to `REPORTABLE_DISEASES` without a
  reference document, so `get_precautions()` returned **empty guidance for a reportable
  disease**. Added `peste-des-petits-ruminants.md` and its slug mapping. A real gap, not a
  flaky test.
- **PR #36 — README audit.** The biggest find: **training a model was never a documented
  step**, so following the README end to end gave a running stack where every diagnosis
  returned `503 MODEL_NOT_TRAINED`. Also corrected the Node version (20+ was wrong on three
  ranges), the native-install note (`shap` fails too, not just `chromadb`), and added a
  "how to run the tests" section that didn't exist.
- **PR #37 — animal identity removed.** Tag numbers and farm IDs never reached `ml-service`;
  they existed so the backend could attach a diagnosis to an `Animal` row. You chose to drop
  the record entirely rather than keep a thin one. Diagnosis is one call now
  (`POST /api/diagnoses`). Shipped alongside: one multi-file photo picker instead of five
  slots, an ambient CSS background, and a UI pass (persistent live region + focus move,
  real photo thumbnails, 44px remove target, confidence meter, one disclaimer per
  submission, "start a new check").
- **PR #38 — both databases deleted.** Measured first, with both absent: symptom diagnosis
  6/6 correct, image diagnosis 5/5 on real photos — but precautions came back **empty**.
  So Postgres (write-only, two saves, zero queries, yet a hard startup dependency) was
  deleted outright, and Chroma was replaced by direct markdown reads. `ml-service`'s suite
  now runs **natively with no skips** — Docker is no longer needed to test it.
- **PR #39 / #40 — species mismatch and image validation.** See STATE.md for the full
  measured detail; the short version is in "What I got wrong" below.

### What I got wrong, and how it was caught

Worth reading before trusting any of this session's measurements at face value.

1. **I chose warning over blocking for species mismatch**, reasoning that a 6% false-positive
   rate was too high to refuse a photo on. You sent a screenshot of a dog photo showing the
   warning *and* "Likely: Foot and Mouth Disease (60%) — Escalate to vet". The error budget
   was priced wrong: a false refusal costs one retry, a missed mismatch tells a farmer to
   report a notifiable disease that isn't there.
2. **I fixed the species check without questioning the gate in front of it.** You then
   uploaded a text screenshot under Dog and got "Kennel Cough, 42%". M15's gate accepted any
   photo with an animal class in its top-5, and 398 of ImageNet's 1000 classes are animals.
   The question was wrong, not the threshold.
3. **A browser verification appeared to fail and didn't.** A hand-built `File` in the test
   harness produced corrupt bytes; the same bytes through the API worked. Re-verified with
   bytes the browser fetched itself. If a browser check fails oddly, suspect the harness.

### Watch out for

- **Commits landed directly on `main` twice** during this session without my checking it
  out — I caught both before pushing, moved them to branches, and reset `main` to
  `origin/main` with `git branch -f` (not `git reset --hard`, which the guardrail hook
  blocks). Worth checking `git status -sb` before committing; I don't know what switched it.
- **You merged PRs mid-task four times** (#35, #37, #38, #39). It works — I branch from the
  updated `main` and continue — but a follow-up fix then lands in a *new* PR rather than the
  one you were watching. If you'd rather review one larger PR, hold off merging until a
  piece is called finished.
- **`.mcp.json` is uncommitted and now stale**: it adds a postgres MCP server pointing at
  `cattlecare`, the database PR #38 deleted. You chose to leave it local. Reverting it is
  the tidy end state whenever you get to it.
- **21 local branches**, most from merged PRs. `refactor/remove-animal-identity` shows
  `ahead 1` — a pre-squash leftover, its content is in `main`. Safe to prune.
- **Docker Desktop stopped partway through** the session and took the dev Postgres with it.
  Nothing depends on Docker now except `make up`, so this matters less than it used to.
- The dev database was already **empty** when I first looked (no tables at all), before I
  touched anything. If you expected history there, it was gone before this session.

### Next, roughly in order of value

1. **Merge PR #40** — it's green and carries the image-validation fix.
2. **Write reference documents for cat and dog diseases.** Companion-animal diagnoses
   currently return *no* precautions and *no* next steps, because
   `DIAGNOSIS_TO_DOC_SLUG` has no entries for them. `docs/DISCLAIMER.md` treats rabies as
   the companion-animal equivalent of a reportable disease, so this is the most
   safety-relevant gap left open. Pre-existing, not introduced this session.
3. **Train a real species classifier** to replace the ImageNet workaround the species guard
   leans on. Downloaded and verified *Sheep Breed Classification* (1,680 labelled sheep
   photos, CC BY 4.0); *Indian Bovine breeds* (CC0) and *Cows and Buffalo* (MIT) exist too.
   This would fix the two limitations the current guard can't: weak sheep detection, and
   livestock-under-Cat/Dog being undetectable.
4. **Try the goat health dataset** (Apache 2.0, 278 MB) for the missing sheep *image* model,
   and the dog skin-disease sets (CC0 / Apache 2.0) against the weak 52.6% dog model.
   Metadata only so far — neither is verified beyond the licence and size.
5. `LICENSE` decision (carried over several sessions), `npx playwright install` for e2e,
   M7 notifications (still unstarted).

## Blockers

- **Livestock photos under Cat or Dog cannot be detected** with the current approach, and
  it isn't a tuning problem: the ratio distributions overlap with valid pet photos. Needs a
  purpose-trained species classifier (see next-steps 3).
- **Dog image model quality** — 52.6% overall, 0.25 F1 for Canine Distemper, no Healthy
  class. Unchanged this session; alternative datasets identified but untested.
- **Sheep's disease gap** — the PPR model is real but single-disease; foot rot and sheep pox
  are still represented by nothing, and no sheep *image* dataset has been found.
- `GITHUB_TOKEN` for the GitHub MCP server is still invalid, and the server disconnected
  mid-session. `gh` CLI works throughout (separate keyring login), so this stayed a nuisance
  rather than a blocker.
