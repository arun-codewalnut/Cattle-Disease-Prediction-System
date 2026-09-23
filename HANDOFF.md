# HANDOFF.md

End-of-session notes. Overwrite this each session — it's a handoff to "next session you"
(or another agent), not a history log (that's what git history / STATE.md decisions are for).

---

## This session (2026-09-23) — branch `feat/m16-goat-species-and-dog-v2`, branched from `main`

You asked to "download the goat dataset and integrate it into our application. If datasets
for other species are available, include them as well to implement support for all species.
Train the model thoroughly." Confirmed scope via `AskUserQuestion` before touching anything:
Goat becomes a full new species (not folded into Sheep), and "other species" work means
replacing the weak Dog model specifically (not a new species-classifier project).

- **Goat added, image-only, real but binary model**: searched Kaggle's public API for
  goat-*disease* image data ("goat disease", "goat skin disease", "goat pox") — nothing found.
  The only real candidate,
  [Healthy and Unhealthy Goat Images](https://www.kaggle.com/datasets/kartikeybartwal/dataset)
  (Apache 2.0, 927 usable images), is binary. Shipped honestly as that: `DISEASES =
  ["Healthy", "Unhealthy"]` in the new `app/models/goat_image_model.py` — **80.1% accuracy,
  0.800 macro F1**. `GOAT` added to `Species` (backend) and `IMAGE_ONLY_SUPPORTED_SPECIES`
  (both services), same pattern Cat/Dog already use. No goat symptom model — the only
  candidate symptom data (the PPR dataset) has an undecodable species column, same wall
  Sheep's own model documents.
- **ImageNet has no goat class** — verified directly against
  `MobileNet_V2_Weights.DEFAULT.meta['categories']`. Used "ibex" (the closest wild-goat proxy)
  in `species_gate.py`'s existing `RUMINANT` group. Measured before shipping (40-photo
  samples): 5% false-reject on real goat photos (in line with other species), 90% cat-as-goat
  caught, only 30% dog-as-goat caught (goat's signal is weaker than cattle's own dedicated
  classes — disclosed, not chased down further this session).
- **Dog retrained on a new dataset**:
  [Dogs Skin disease dataset](https://www.kaggle.com/datasets/yashmotiani/dogs-skin-disease-dataset)
  (CC0, 439 images). Disease list changes entirely — from the old systemic list (Canine
  Distemper/Parvovirus/Kennel Cough/Mange, no Healthy class) to a skin-disease list (Bacterial
  Dermatosis/Fungal Infection/Healthy/Hypersensitivity-Allergic Dermatosis), the same "swap in
  real data over prior research" call M13 made for Cat. **Real result: 70.5% accuracy, 0.683
  macro F1** (was 52.6%/0.489) — and finally a real Healthy class. This directly disproves a
  prior session's blocker note guessing that "close-up skin shots" wouldn't help Dog's
  accuracy — they did, substantially; the old systemic-disease list was the actual problem,
  not the photo style.
- **A real, unplanned regression, measured rather than assumed away**: swapping Dog's dataset
  to skin close-ups dropped the species-mismatch detector's dog-as-cow catch rate from ~80%
  (old whole-body photos) to ~30% — close-ups don't show the face/ears/snout signal the
  detector needs. Accepted as a tradeoff (the real Dog-accuracy gain was judged worth it), but
  not silently absorbed: `docs/DECISIONS.md` has the full measurement, and
  `tests/test_species_mismatch.py`'s dog-mismatch test now reads a retained
  `data/dog-images-v1-superseded/` folder specifically, so that test still proves the
  detector's real capability independent of which dataset trains today's disease classifier.
- Also fixed along the way: Cat/Dog's `REGISTRY.md` rows had gone stale/duplicated again (same
  append-not-replace training-script behavior PR #32 already hit once) — cleaned up manually.
  Added 4 new hand-written reference docs (`bacterial-dermatosis.md`, `fungal-infection.md`,
  `hypersensitivity-allergic-dermatosis.md`, `unhealthy-goat.md`) so these new diagnoses carry
  real precautions/next-steps instead of falling into the pre-existing Cat-only gap.
- Docs updated: `docs/specs/M16-goat-disease-detection.md` (new), `docs/specs/
  M14-dog-disease-detection.md` (new "Follow-up" section), `docs/DISCLAIMER.md`,
  `docs/API_CONTRACTS.md`, `docs/ROADMAP.md`, `docs/DECISIONS.md` (2 new entries), `STATE.md`.
- **Validated**: ml-service 94 passed / 1 skipped, backend `mvn -q test` clean (32 tests,
  0 failures), frontend lint clean + 27/27 tests + production build. Live end-to-end
  verification against the real running stack is the next step before calling this fully
  done — see below.

### What shipped

- **Live end-to-end verification done this session**, against the real running stack — but
  hit a real environmental snag worth knowing about: another chat session already had
  `ml-service` running on the default port 8000 (and `frontend` on 5173) with **old code, no
  Goat model**. The first verification pass silently hit that stale instance through the
  default `ML_SERVICE_BASE_URL` and returned a cattle-model disease ("Lumpy Skin Disease") for
  a goat photo — looked exactly like a real routing bug until `netstat` showed the port
  collision. Re-ran everything on `ml-service:8001` / `frontend:5174` (backend on `8080` was
  actually free) with `ML_SERVICE_BASE_URL`/`CORS_ALLOWED_ORIGINS` env vars pointed
  accordingly — confirmed clean after that: goat healthy/unhealthy photos both correctly
  routed to the goat model and distinguished, dog photos correctly hit the new skin-disease
  classes, a cat photo submitted as Goat correctly triggered `species_mismatch`, Cow/Cat
  symptom and image paths regression-free, all verified through curl against the real backend
  and visually in the browser (species dropdown, disclosure text, a full Cow symptom
  submission rendering a real result). **If ports 8000/5173 are busy next session, check
  `netstat` before trusting a "green" verification** — a bound-but-wrong-code stale process
  looks identical to success at the HTTP level.
- **Nothing has been committed or pushed yet** — everything above is sitting in the working
  tree on `feat/m16-goat-species-and-dog-v2`. Ask before committing/pushing.
- Real goat/dog training data now lives under `ml-service/data/goat-images/` and
  `ml-service/data/dog-images/` (both gitignored, as usual) — `SOURCE.md` in each has the
  exact `kagglehub` redownload command if a fresh clone needs it.
- The old Dog v1 photos are kept at `ml-service/data/dog-images-v1-superseded/` — deliberately
  not deleted, since a test now depends on it (see above). Don't clean it up without checking
  the test still has a photo source.
- Dog's Bacterial Dermatosis class is still the weakest (0.52 F1, recall ~42%) — real, not
  fixed this session; more/better data for that specific class would be the next lever if Dog
  accuracy is revisited again.
- Two flagged-but-unused Dog candidates from this session's research, if a future session
  wants to push Dog further: `diemhuongnt12/5-skin-dog-diseases`'s `dataset1/` (demodicosis +
  ringworm, 2 disease classes not in the current model at all, but YOLO-detection format with
  likely Roboflow-augmented duplicates — would need dedup work before trusting any accuracy
  number from it).
- Sheep's remaining gap (no foot rot/sheep pox coverage) is unaffected by this session, still
  open if ever prioritized.
- Decide on a `LICENSE` (still open, carried over from several sessions back).
- M7 (notifications, issue #7) still open and unstarted, independent of everything above.
- `npx playwright install --with-deps chromium` in `tests/e2e/` — still not done.
- There's a separate `docs/session-handoff-and-state` branch (not merged to `main`) with a
  newer STATE.md/HANDOFF.md covering a *different* prior session's work (species-mismatch
  detection tuning, image-validation retuning, DECISIONS.md entries dated 2026-09-23 under a
  "session 14" label) that this branch's `STATE.md` doesn't yet include, since this branch was
  cut from `main` before that PR merged. Whoever merges next should check both land cleanly —
  this session's `STATE.md`/`HANDOFF.md` edits were made against the older, pre-merge version.

## Blockers

- None new. The Dog-accuracy blocker from the prior session's HANDOFF is resolved (see above)
  — its "different kind of data" hypothesis was directionally right, though the real fix was
  swapping *what disease category* the data covers (skin vs. systemic), not just photo framing.
- `GITHUB_TOKEN` used by the GitHub MCP server was noted as invalid in a prior session — not
  re-verified this session, since no GitHub MCP/`gh` calls were needed.
