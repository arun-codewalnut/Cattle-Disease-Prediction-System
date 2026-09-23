# Spec: Remove both databases — Chroma and Postgres

**Milestone**: stretch (post-M15 refactor)
**Status**: agreed

## Actor + goal

A developer runs the stack and gets identical diagnosis behaviour with no database of any
kind. Measured before writing this spec, with Postgres absent and `chromadb` not installed:

- symptom diagnosis — **6/6 scenarios correct** (FMD 100%, LSD 90%, Mastitis 84%, BRD 88%,
  Healthy 99%, Sheep PPR 93%), escalation correct for both reportable diseases;
- image diagnosis — **5/5 real labelled photos correct**, and the M15 non-animal gate still
  returned `invalid_image` / `retry_upload`.

So neither database contributes to a diagnosis. What they do contribute:

- **Postgres**: nothing readable. Two `save()` calls, zero queries, no history endpoint — but
  it is a hard startup dependency (Flyway fails context initialisation, so the backend does
  not boot without it).
- **Chroma**: the precautions and next-steps text, which came back **empty** without it —
  including for Foot and Mouth Disease, where the farmer was told to escalate with no
  guidance at all. That content is six hand-written markdown files totalling **10.8 KB**,
  fetched by exact key; the vector database is not what makes it work.

The goal is to delete both while keeping every user-visible behaviour, including precautions
and next steps, byte-identical.

## Boundaries & failure states

- **Precautions/next-steps must be identical**, not approximated. Same text, same order, for
  every diagnosis. This is the one thing the change could plausibly break, and
  `docs/DISCLAIMER.md` makes it safety-relevant for reportable diseases.
- **`retrieve()` becomes an exact diagnosis→document lookup** rather than a similarity
  search. This is a deliberate behaviour change and a narrowing: previously a query could
  surface another disease's chunk, which was never desirable. It can now only return the
  matching document's overview, or nothing.
- **The explain node's contract is unchanged**: retrieval failure still degrades to `[]` and
  the deterministic template, and the LLM is still optional.
- **`sources` stays in the API response.** It is still accurate — it names the document the
  explanation drew on. The frontend never reads it, but `docs/API_CONTRACTS.md` documents it.
- **`DiagnosisCaseResponse.id` is removed**, because nothing is persisted, so there is no row
  to identify. `createdAt` stays — it is generated at response time and still true. The
  correlation ID remains the handle for tracing a request across services.
- **No diagnosis history.** Cases are no longer recorded anywhere. This is the accepted cost;
  if history returns it returns as a new spec with a read path, not by reviving this one.
- `ml-service` must keep working when the reference documents directory is missing or a file
  is unreadable — return empty lists, never raise, same principle as today.
- Migrations `V1`–`V4` are deleted outright rather than superseded by a `V5` drop, because
  the entire Flyway apparatus goes with them. Existing local databases are simply abandoned;
  nothing reads them.

## Examples

**Precautions lookup** — `get_precautions("Foot and Mouth Disease")` reads
`data/veterinary-reference/foot-and-mouth-disease.md` and returns, exactly as today:
```json
{
  "precautions": ["Isolate the affected animal from the rest of the herd immediately.", "..."],
  "next_steps": ["Contact your veterinarian or local animal health authority immediately — ...", "..."]
}
```

**Retrieval** — `retrieve("Lumpy Skin Disease")` returns that document's overview blocks as
`[{"text": ..., "source": "lumpy-skin-disease"}, ...]`; `retrieve("Not A Disease")` returns
`[]`.

**Backend response** — `POST /api/diagnoses` returns the same JSON minus `id`:
```json
{ "species": "COW", "diagnosis": "Foot and Mouth Disease", "confidence": 0.81,
  "explanation": "...", "recommendedAction": "escalate_to_vet",
  "precautions": ["..."], "nextSteps": ["..."], "createdAt": "..." }
```

**Edge case — reference docs missing entirely**: both functions return empty, the diagnosis
still succeeds, exactly as a Chroma failure degraded today.

## Not in scope

- Any change to the models, the agent graph's structure, species routing, the image quality
  gate, or the disease lists.
- Re-adding diagnosis history in any form.
- Changing the reference documents' content.
- The `app/rag/` package name. It is still retrieval-augmented generation — the retrieval
  source changes from a vector store to the filesystem, the augmentation does not.

## Acceptance criteria (must be checkable)

- [ ] `chromadb` appears in no source file, no `requirements.txt`, and no Dockerfile.
- [ ] `ml-service`'s **full** test suite passes in the native Windows venv with no skips for
      missing `chromadb` — i.e. Docker is no longer required to test this service.
- [ ] For every diagnosis in `DIAGNOSIS_TO_DOC_SLUG`, `get_precautions()` returns exactly what
      it returned with Chroma (captured before the change and compared afterwards).
- [ ] No file under `backend/src` references JPA, Flyway, a `DataSource`, `DiagnosisCase`, or
      `DiagnosisCaseRepository`; `backend/src/main/resources/db/` no longer exists.
- [ ] `backend/pom.xml` has no `data-jpa`, `flyway`, or `postgresql` dependency.
- [ ] `cd backend && mvn -B verify` passes **with no database running**.
- [ ] `docker-compose.yml` defines only `ml-service`, `backend`, `frontend` — no `postgres`,
      no `chroma`, no volumes.
- [ ] `.github/workflows/ci.yml`'s backend job has no `services:` block.
- [ ] Symptom and image diagnosis still produce the results measured above, verified by
      running the app, not only the suites.

## Agent mirror-back (fill before coding starts)

**Intent**: delete both databases and every artefact that exists only to serve them, while
keeping behaviour identical — including the precautions/next-steps text, which is the only
user-visible thing either database currently provides.

**Inputs/outputs that change**:
- `retrieve(query, k, persist_dir)` → `retrieve(diagnosis, k, docs_dir)`; exact lookup, not
  similarity search.
- `get_precautions(diagnosis, persist_dir)` → `get_precautions(diagnosis, docs_dir)`; same
  return shape.
- `POST /api/diagnoses` and `/api/diagnoses/image` responses lose `id`.
- `ml-service` gains no dependency; it loses `chromadb`.

**Assumptions I had to make** (flagging rather than silently choosing):
1. **The markdown parser moves rather than dies.** `_parse_sections`/`_slugify` currently live
   in `app/rag/ingest.py` and are already covered by `tests/test_ingest.py`. They move into
   `retrieval.py` and keep their tests; `ingest.py` itself is deleted, since there is nothing
   left to ingest into.
2. **Documents are read on demand and cached in a module-level dict**, mirroring the existing
   `_collection_cache`. The corpus is 10.8 KB, so this is cheap, and it keeps a file edit
   visible after a restart without an ingest step.
3. **`id` is dropped from the response rather than synthesised.** A random per-response id
   would look like a durable identifier that could be looked up, which would be a lie.
4. **`V1`–`V4` are deleted, not superseded.** A `V5__drop_everything.sql` would only matter if
   something still ran Flyway, and nothing will.
5. The `chroma` service in `docker-compose.yml` was already unused (M6 used embedded Chroma),
   so removing it changes nothing at runtime.
