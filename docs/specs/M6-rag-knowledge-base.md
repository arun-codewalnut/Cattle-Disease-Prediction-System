# Spec: RAG knowledge base (Chroma)

**Milestone**: M6
**Status**: done

## Actor + goal

Before the `explain` node (M5) asks an LLM to write an explanation, it retrieves relevant
passages from a small veterinary reference knowledge base (stored in Chroma) about the
diagnosed disease, and gives those passages to the LLM as grounding context — so the
explanation can reference real material instead of only the bare
diagnosis/confidence/top_features M5 had access to. The `sources` field (always `[]` since
M2) starts reflecting what was actually retrieved and used.

## Boundaries & failure states

- **Retrieval failure degrades gracefully, same principle as M5's LLM failure.** If Chroma
  is unreachable/errors/returns nothing, `explain` proceeds exactly as M5 did — LLM call
  with no retrieved context, or the template fallback — never a crash.
- **`sources` only lists documents that were actually used to generate the shown
  explanation.** If the LLM call fails and `explain` falls back to the deterministic
  template (which doesn't cite anything), `sources` is `[]` for that response — no claiming
  a citation that isn't really reflected in the text.
- **The LLM still cannot invent facts beyond what it's given** — the prompt constrains it
  to the diagnosis/confidence/top_features (M5) *plus* the retrieved passages (M6), nothing
  else. Same non-negotiable rule as M5, extended to cover the new context.
- **No retrieval attempted for `"uncertain"` diagnoses** — there's no disease to look up
  reference material for.

## Examples

**Retrieval**: given diagnosis `"Foot and Mouth Disease"`, `retrieve()` returns the most
relevant chunks from `foot-and-mouth-disease.md` (paragraph-level chunks), each tagged with
its source document.

**Explain node behavior with retrieval**:
```json
{
  "diagnosis": "Foot and Mouth Disease",
  "confidence": 0.81,
  "explanation": "This points to Foot and Mouth Disease — a highly contagious viral disease affecting cloven-hooved animals, typically causing fever and blister-like lesions in the mouth and on the feet, consistent with the symptoms observed...",
  "recommended_action": "escalate_to_vet",
  "sources": ["foot-and-mouth-disease"]
}
```

**Edge case — Chroma unavailable or empty collection**: same response shape, `sources: []`,
`explanation` falls back to M5's behavior (LLM without retrieved context, or the template).

## Not in scope

- A general-purpose document upload/management UI — the knowledge base is a fixed, small,
  hand-curated set of reference files ingested via one script, not a dynamic content system.
- Any change to the diagnosis, confidence, or `REPORTABLE_DISEASES` escalation logic — same
  boundary M5 already established, unchanged here too.
- Networked Chroma server (the `chroma` service already sitting unused in
  `docker-compose.yml` since the original scaffold) — see deviation #2 below.

## Acceptance criteria

- [x] `ml-service/data/veterinary-reference/` holds one reference document per diagnosable
      disease (FMD, LSD, Mastitis, BRD), plus a `SOURCE.md` documenting what they are and
      aren't (see deviation #1).
- [x] `app/rag/ingest.py` chunks (paragraph-level) and upserts those documents into a Chroma
      collection, runnable standalone (`python -m app.rag.ingest`), same pattern as
      `training/symptom_model_train.py`.
- [x] `app/rag/retrieval.py` implements `retrieve(query: str, k: int = 3) -> list[dict]`
      returning chunks with their source document identifier.
- [x] `explain` node in `app/agent/graph.py` calls `retrieve(diagnosis)` before building the
      LLM prompt (skipped entirely for `"uncertain"`), includes retrieved passages in the
      prompt, and sets `sources` to the retrieved documents' identifiers — only when the LLM
      call (using that context) actually succeeds.
- [x] Retrieval failure (Chroma error, empty collection) doesn't block diagnosis — same
      try/except-and-degrade pattern as M5's LLM failure handling.
- [x] Tests cover: retrieval returns expected chunks for a known query, `explain` includes
      retrieved context in the sources it reports on success, retrieval failure still
      produces a full diagnosis response, and `"uncertain"` never triggers retrieval —
      running via Docker (see deviation #3), not the native venv. **29/29 passing.**
- [x] `docs/API_CONTRACTS.md` updated: `sources` is no longer always `[]`.

## Verification note

One test assertion (`test_sources_populated_when_llm_and_retrieval_both_succeed`) initially
asserted `sources == ["foot-and-mouth-disease"]` exactly and failed — semantic retrieval
over small, thematically-similar reference docs legitimately also surfaced a Lumpy Skin
Disease passage (both docs use similar viral-cattle-disease language). This isn't a bug;
the assertion was too strict. Fixed to check the correct primary source is present, not
that it's the only one.

Also found (while committing): the `conftest.py` RAG-ingestion fixture being `autouse`
session-scoped meant its `ImportError` (no `chromadb` natively) broke **all 29 tests**, not
just RAG ones. Fixed with the same graceful-degradation pattern used everywhere else in
this project — see `docs/DECISIONS.md`. Native `pytest` now correctly shows 24 passed, 2
skipped (clear reasons), 0 errors; Docker still shows 29/29.

## Agent mirror-back

**Intent**: add a retrieval step ahead of the existing `explain` node, backed by a small,
fixed, locally-embedded knowledge base — not a new node type, not a change to anything
upstream of `explain`.

**Inputs/outputs**: unchanged from M5's `run_diagnosis()` signature and response shape —
`sources` simply starts containing real values instead of always `[]`.

**Assumptions flagged before coding**:
1. **The reference documents are original, hand-written educational summaries, not scraped
   or copied from any specific external source.** Same reasoning as M1's synthetic
   dataset: reproducing real copyrighted veterinary textbook content isn't appropriate, and
   there's no confirmed freely-licensed veterinary corpus readily available here. Each
   document is a short, general factual summary (symptoms, transmission, general
   management) written for this learning project, explicitly not a substitute for real
   veterinary literature — documented in `SOURCE.md`, consistent with
   `docs/DISCLAIMER.md`.
2. **Chroma runs embedded (`chromadb.PersistentClient`), not as the separate networked
   server already defined (unused) in `docker-compose.yml`.** Simpler: no server process to
   run/coordinate, same free/local embedding function either way (Chroma's bundled default,
   no API key), and easier to test (point at a temp directory, no network). The
   `docker-compose.yml` `chroma` service stays defined but becomes unnecessary — not
   removed in this milestone, flagged in `docs/DECISIONS.md` for a future cleanup pass.
3. **`chromadb` cannot be installed natively in this Windows/Python 3.13 dev environment —
   confirmed, not assumed.** Checked `chroma-hnswlib`'s latest PyPI release (0.7.6): no
   `cp313` wheel exists for any platform, Windows included, so this isn't fixable by
   picking a different version — it needs either Microsoft C++ Build Tools or Docker. Since
   Docker is already a required tool for this project (backend tests need it for Postgres),
   this milestone's tests run via `docker build`/`docker run` against `ml-service`'s
   existing `Dockerfile` (which already has `build-essential`) rather than the native venv.
   `ml-service/AGENTS.md`'s existing known-gap note already flagged this exact scenario.
