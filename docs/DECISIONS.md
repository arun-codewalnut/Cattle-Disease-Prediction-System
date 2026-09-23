# Decisions Log

Lightweight ADR (architecture decision record) log. Add a new entry when a non-obvious
choice is made — this stops future sessions (agent or human) from re-litigating or
silently drifting from a decision.

**Format for new entries**: Decision, Why, and where relevant, **Alternatives** (what else
was considered and why it lost) and **Consequences** (what this commits us to). Not every
entry needs all four — a one-line "why" is fine for small calls.

**Supersede, don't overwrite.** If a decision changes, add a new entry that says
`Supersedes: <date/title>` rather than editing or deleting the old one — the trail of *why*
matters as much as the current answer.

---

### 2026-09-16 — Polyglot split: Java backend + Python ML/agent service + React frontend

**Decision**: Java Spring Boot for the API gateway/business logic, Python FastAPI + LangGraph
for ML inference and agent orchestration, React for UI.

**Why**: Matches existing skills (React + Java). ML/agent ecosystem (XGBoost, PyTorch,
LangGraph, RAG libraries) is Python-first — reimplementing that in Java isn't worth it for a
learning project. Two services over REST keeps the boundary simple and language-agnostic.

---

### 2026-09-16 — Free/open-source tooling only

**Decision**: Ollama (local LLM) or free API trial tiers instead of paid LLM APIs; Chroma
instead of Pinecone; Flyway (free) for migrations; Render/Railway/Vercel/Supabase free tiers
for hosting; email/WhatsApp Cloud API free tier instead of Twilio.

**Why**: This is a learning project — no budget, and free tools are sufficient to learn the
same architectural patterns as paid ones.

---

### 2026-09-16 — Agent orchestration lives in `ml-service`, not `backend`

**Decision**: LangGraph agent code lives entirely in the Python service. Java `backend`
treats it as an opaque REST dependency (`POST /agent/diagnose`).

**Why**: LangGraph/LangChain are Python-native; keeping orchestration logic split across two
languages would make the agent's control flow harder to reason about for no benefit.

---

### 2026-09-16 — Agent-context files: root + per-service, `AGENTS.md` canonical

**Decision**: `AGENTS.md` is canonical/tool-agnostic; `CLAUDE.md` files `@import` it. Root
files cover cross-cutting concerns; each service has its own scoped `AGENTS.md`/`CLAUDE.md`
for stack-specific conventions. Claude Code skills live in `.claude/skills/*/SKILL.md` as
thin adapters over `agents/playbooks/*.md` (the actual tool-agnostic content).

**Why**: `AGENTS.md` is an emerging real cross-tool standard; `.claude/skills/` is Claude
Code-specific and has no equivalent in other tools yet, so content is kept in one
tool-agnostic place and adapted per-tool rather than duplicated.

---

### 2026-09-16 — Added CONTRIBUTING.md, DISCLAIMER.md, and GitHub issue/PR templates

**Decision**: `CONTRIBUTING.md` (branch/commit/PR conventions), `docs/DISCLAIMER.md` (the
"not a certified vet tool" safety constraint), YAML-form issue templates
(`.github/ISSUE_TEMPLATE/bug_report.yml`, `feature_request.yml`) and
`.github/PULL_REQUEST_TEMPLATE.md`.

**Why**: The vet-safety disclaimer had only ever been discussed in conversation, never
written into the repo — a real gap for a health-adjacent tool. The GitHub templates make the
milestone-driven issue/PR workflow (already assumed by `AGENTS.md`'s "reference the
milestone/issue" convention) actually concrete instead of implied.

---

### 2026-09-16 — Implemented CodeWalnut's 12 agentic-engineering competencies

**Decision**: Added concrete, working infrastructure for all 12 (Toolchain Setup, Spec
Framing, Context Engineering, Test Automation, Skill Packaging, Multi-Agent Workflows,
Docs & Diagrams, Evidence-led PRs, Code Review, Token Economics, Agentic Refactoring,
Agentic Retrospective) rather than just documenting the intent. Key additions: `PreToolUse`/
`Stop` guardrail hooks (`.claude/hooks/`) + permission deny rules; `docs/specs/` with a
worked M1 spec; `docs/REPO_MAP.md`; Vitest (frontend) + Playwright (`tests/e2e/`) wired up
and passing; a `retrospective` skill/playbook; Mermaid diagrams in `docs/ARCHITECTURE.md`;
a real `.githooks/pre-commit`; explicit `/code-review` + model/effort guidance in root
`AGENTS.md`.

**Why**: The user asked for all 12 to be genuinely implemented, not just planned. Several
(Test Automation, Code Review, Agentic Refactoring) can't be fully exercised yet since no
real feature code exists — for those, what's implemented is the *process and tooling*
(strategy doc, working smoke test, playbook), ready for when M1+ lands, documented honestly
as such rather than faked.

**Consequences**: fresh clones must run `git config core.hooksPath .githooks` once (not
git-tracked, per-clone config — see `CONTRIBUTING.md`). The `PreToolUse` Bash hook adds a
small latency per Bash call in exchange for a real safety net — verified working (blocks a
force-push pattern, allows normal commands) during implementation.

---

### 2026-09-16 — GitHub MCP server: switched to the official Docker image

**Decision**: `.mcp.json`'s `github` entry now runs `docker run -i --rm -e
GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server` instead of `npx -y
@modelcontextprotocol/server-github`.

**Why**: User has the official image already. Community npx-based server worked
mechanically (tools loaded) but authentication never succeeded due to `GITHUB_TOKEN` not
propagating from `setx` into the already-running Claude Code process (a Windows
Explorer-environment-caching issue, not a config bug).

**Consequences**: still substitutes `${GITHUB_TOKEN}` from Claude Code's own process
environment — the same propagation problem can recur unless the token is instead set via
`claude mcp add --scope user -e GITHUB_PERSONAL_ACCESS_TOKEN=...` (stored directly in
Claude Code's own config, bypassing OS env vars entirely). Requires Docker Desktop running
locally, confirmed present (v29.7.2).

---

### 2026-09-16 — Dropped deployment milestone (M8); GitHub Milestones/Issues created via `gh` CLI

**Decision**: M8 (deployment) removed from `docs/ROADMAP.md` entirely — this stays a
local/learning project, not something hosted for real users. M1–M7 created as real GitHub
Milestones (not just numbered titles) with matching issues (#1–#7), each with a description,
acceptance criteria, dependency note, and — where no spec exists yet — an explicit pointer
to write one before starting, per the spec-first convention.

**Why**: User explicitly said M8 isn't required. The GitHub MCP server's `GITHUB_TOKEN`
turned out to be a genuinely invalid token (confirmed via `gh auth status`), not an
environment-propagation issue — but `gh` CLI had a separate, working keyring credential
(`arun-codewalnut`, `repo` scope) the whole time, unaffected by the bad `GITHUB_TOKEN` env
var once explicitly unset for the command (`env -u GITHUB_TOKEN gh ...`). Used that instead
of continuing to debug the MCP path.

**Consequences**: if `GITHUB_TOKEN` is ever fixed/removed from the environment, `gh`'s
keyring credential becomes the default again with no special handling needed. Future
GitHub-related work in this repo should default to `gh` CLI via Bash (matching the general
guidance to use `gh` for GitHub tasks), not the MCP server, unless the MCP token issue is
separately resolved.

---

### 2026-09-16 — M1 implemented with a synthetic dataset, not a real public one

**Decision**: `ml-service/training/generate_synthetic_data.py` generates a documented,
clearly-labeled synthetic symptom/disease dataset (5 classes, 750 rows); the M1 model is
trained on that, not a real dataset.

**Why**: no genuinely public, auth-free, ML-ready cattle-disease dataset was reliably
fetchable in this environment — the well-known ones are Kaggle-hosted and need account/API
auth. Blocking the whole M1→M7 pipeline on dataset sourcing wasn't worth it for a learning
project; this keeps training → inference → tests real and working end to end.

**Consequences**: model quality (88.8% CV accuracy) reflects synthetic, cleanly-separable
symptom profiles, not real-world diagnostic difficulty — don't read too much into the
numbers. Swapping in a real dataset later only requires replacing
`ml-service/data/symptom_dataset.csv` (same schema) and re-running training; no code changes
needed in `app/models/symptom_model.py` or `training/symptom_model_train.py`. Full rationale
in `ml-service/data/synthetic-symptom-dataset/SOURCE.md`.

---

### 2026-09-16 — All-missing-symptoms input is explicitly short-circuited, not model-inferred

**Decision**: `predict()` returns a hardcoded uniform-prior confidence (`1/len(DISEASES)`)
and `"uncertain"` when zero symptom fields are provided, without calling the model at all.

**Why**: empirically, XGBoost's learned missing-value default-routing produced a *confident*
prediction ("Bovine Respiratory Disease", >0.4) for an all-NaN input during testing — a
training-time artifact, not a real signal. The spec requires this case to report low
confidence; trusting the raw model output here would have been dishonest.

**Consequences**: this is a narrow special case (exactly zero evidence) — any partial input
(even one symptom provided) still goes through the real model with native NaN handling for
the rest.

---

### 2026-09-16 — Backend `mvn test` needs a real Postgres; CI now provides one

**Decision**: `.github/workflows/ci.yml`'s `backend` job now runs a `postgres:16-alpine`
service container. `backend/AGENTS.md` documents the local equivalent.

**Why**: discovered while running the full build/test suite for issue #1 — the default
`BackendApplicationTests.contextLoads()` boots the full Spring context, which runs Flyway on
startup and fails without a reachable Postgres. This was a latent bug that would have
silently broken CI on the very first PR touching `backend`. Not introduced by M1 (M1 only
touched `ml-service`) — just the first time `mvn test` (not `mvn compile`) was actually run
end-to-end.

---

### 2026-09-16 — M2 branched from M1's branch, not from `main`

**Decision**: `feat/m2-wire-model-into-agent` was created off `feat/m1-baseline-symptom-model`,
not off `main`.

**Why**: M2 directly depends on M1's code (`app/models/symptom_model.py`, `training/`), and
M1's PR (#8) isn't merged yet. Branching from `main` would mean M2's code doesn't
compile/import until M1 lands. This is a stacked-branch pattern — M2's PR should be
reviewed/merged after M1's, or rebased onto `main` post-merge.

---

### 2026-09-16 — Escalation logic is a fixed lookup table, not model-driven

**Decision**: `REPORTABLE_DISEASES` in `ml-service/app/agent/graph.py` is a hardcoded set
(`{"Foot and Mouth Disease", "Lumpy Skin Disease"}`) that always forces
`recommended_action: "escalate_to_vet"`, regardless of the model's confidence score.

**Why**: this is the concrete enforcement of `docs/DISCLAIMER.md`'s safety constraint. A
rule this consequential shouldn't be something the model could silently drift on as it's
retrained — it needs to be auditable in a code diff, not buried in learned weights.

**Consequences**: adding a new reportable disease later means editing this list explicitly
(and ideally a test alongside it), not just retraining the model with new data.

---

### 2026-09-16 — M3 branched from `main`, not from M1/M2's branches

**Decision**: `feat/m3-backend-domain-model` branches off `main` (which has M1 merged, not
M2 yet — see the M2 catch-up PR #10), unlike M2 which stacked on M1's branch.

**Why**: M2 genuinely needed M1's Python files to import (same service, real code
dependency). M3 is backend Java code calling `ml-service` over HTTP at runtime — the two
services are decoupled by the REST boundary, so M3's code doesn't need M1/M2's Python files
physically present in its branch to compile or unit-test. Branching from `main` avoids
unnecessary stacking depth for a milestone that doesn't actually need it.

---

### 2026-09-16 — `RestClient.Builder` isn't auto-configured; call `RestClient.builder()` directly

**Decision**: `MlServiceClient` calls the static `RestClient.builder()` factory method
directly instead of injecting a Spring-managed `RestClient.Builder` bean.

**Why**: discovered while running M3's tests — `BackendApplicationTests.contextLoads()`
failed with `NoSuchBeanDefinitionException` for `RestClient.Builder`. In this Spring Boot 4
setup (with the granular `spring-boot-starter-webmvc` rather than a monolithic `-web`
starter), `RestClient` auto-configuration isn't pulled in automatically. Rather than chase
down which specific starter module provides it, calling the static factory sidesteps the
question entirely — `RestClient.builder()` needs no Spring context at all.

**Consequences**: if a later milestone wants Spring-managed `RestClient` customization
(e.g. a shared interceptor across multiple clients), revisit this — it may be worth finding
and adding the right starter at that point instead of duplicating config per-client.

---

### 2026-09-17 — CORS wasn't configured on `backend`; added `WebConfig`

**Decision**: `backend/src/main/java/com/cattlecare/backend/config/WebConfig.java` (new) —
a `WebMvcConfigurer` allowing `cors.allowed-origins` (default `http://localhost:5173`) on
`/api/**`.

**Why**: discovered by actually running the full stack and submitting M4's form in a real
browser — every call from `frontend` to `backend` was blocked outright by the browser's
CORS preflight check, since nothing in `backend` ever set
`Access-Control-Allow-Origin`. No unit test catches this class of bug — it only shows up
with a real browser making a real cross-origin request. This is exactly why UI milestones
get manually verified in a browser, not just unit-tested with mocks (see
`agents/playbooks/run-stack.md` and the project's testing convention).

**Consequences**: `cors.allowed-origins` will need updating (or becoming a list) if/when
`frontend` is ever deployed somewhere other than `localhost:5173` — out of scope for now
(deployment is explicitly out of scope, see the M8-dropped decision above), but worth
remembering when that changes.

---

### 2026-09-17 — `MlServiceClient` forces HTTP/1.1 (JDK HttpClient vs. uvicorn incompatibility)

**Decision**: `MlServiceClient` now builds its own `java.net.http.HttpClient` with
`.version(HttpClient.Version.HTTP_1_1)` and passes it to `RestClient` via
`JdkClientHttpRequestFactory`, instead of using `RestClient`'s default request factory.

**Why**: also discovered via the same live end-to-end browser test — the diagnosis call from
`backend` to `ml-service` failed with an opaque "ml-service returned an error: 400 Bad
Request" until checking `ml-service`'s own logs, which showed `WARNING: Unsupported upgrade
request.` / `WARNING: Invalid HTTP request received.`. Root cause: the JDK `HttpClient`
underlying `RestClient` defaults to attempting an HTTP/2-cleartext upgrade (`Upgrade: h2c`)
on the first request, which uvicorn's HTTP/1.1-only server rejects at the protocol level —
before the request ever reaches FastAPI's routing or Pydantic validation. Another case a
mocked unit test can't catch — this only appears when two real HTTP implementations
actually talk to each other.

**Consequences**: any future new HTTP client added in `backend` talking to `ml-service` (or
any other plain HTTP/1.1 server) needs the same explicit HTTP/1.1 pin — this isn't
`ml-service`-specific, it's a JDK `HttpClient` default that surprises any HTTP/1.1-only
server.

---

### 2026-09-17 — M5: LangGraph restructure improves explanation quality, not diagnosis accuracy

**Decision**: `run_diagnosis()` is now a compiled LangGraph `StateGraph`
(`intake → route → predict_symptoms|predict_image → explain → recommend`) instead of one
plain function. `explain` calls an LLM (via `app/agent/llm.py`'s `get_llm()` abstraction,
provider-swappable, local Ollama by default) to generate the explanation text, falling back
to the old deterministic template on any failure.

**Why**: this is explicitly *not* meant to improve diagnostic accuracy — the XGBoost model,
its confidence score, and the `REPORTABLE_DISEASES` escalation rule are all byte-for-byte
unchanged from M1/M2. Only the `explanation` field's content changes (LLM-generated,
grounded strictly in the model's own output — not new medical claims). This distinction
was worked out explicitly with the user before implementation, precisely to avoid the
"it's using AI now, so it must be more medically right" misconception for a health-adjacent
tool. See the M5 spec's opening section.

**Alternatives considered**: a free-form agent loop (LLM decides what to call next) —
rejected, same reasoning as the spec: a diagnosis tool needs every path through the system
known in advance, not improvised.

**Consequences**:
- New dependency: `langchain-ollama==0.2.2`, chosen specifically because it's the newest
  release still compatible with the already-pinned `langchain-core==0.3.28` — newer
  `langchain-ollama` releases require `langchain-core>=0.3.33` or (as of `1.1.0`) `>=1.2`,
  which would force an unplanned `langchain-core`/`langgraph` upgrade. Revisit this pin
  together if a future milestone needs a newer `langchain-core`.
- Test suite runtime regression, found and fixed in the same session: with no mocking,
  every confident-diagnosis test was trying to actually reach Ollama (not installed in this
  environment) and waiting out a connection timeout — 15 tests went from ~2s to ~25s total.
  Fixed with an autouse `conftest.py` fixture that makes `get_llm()` raise immediately by
  default (this is also the *honest* default, since Ollama genuinely isn't running here),
  with individual tests overriding it locally to test the LLM-success path. Runtime back to
  ~2s for 21 tests.
- Confirmed via `where ollama` that Ollama isn't installed in this dev environment, so the
  LLM-success path is only tested via mocks here — a live check is a bonus for whoever
  installs Ollama locally, not a requirement of "done" for this milestone (see the spec's
  mirror-back).

---

### 2026-09-17 — M6: Chroma runs embedded, not as the networked docker-compose service

**Decision**: `app/rag/retrieval.py` uses `chromadb.PersistentClient` (embedded, writes to
`ml-service/data/chroma_db/`, gitignored) instead of connecting to the separate `chroma`
service already defined (unused since the original scaffold) in `docker-compose.yml`.

**Why**: no server process to run/coordinate, same free local embedding function either
way (Chroma's bundled default — no API key), and far easier to test (point at a temp
directory, no network dependency at all).

**Consequences**: `docker-compose.yml`'s `chroma` service and `CHROMA_HOST`/`CHROMA_PORT`
in `.env.example` are now genuinely unused — not removed in this milestone (kept the diff
focused), flagged here for a future cleanup pass. `ml-service/AGENTS.md` documents the new
persistence path.

---

### 2026-09-17 — M6: reference knowledge base is original hand-written content

**Decision**: `ml-service/data/veterinary-reference/*.md` are original, hand-written
educational summaries (symptoms, transmission, general management) for the 4 diagnosable
diseases — not scraped, copied, or sourced from any specific external document.

**Why**: same reasoning as M1's synthetic dataset. No confirmed freely-licensed veterinary
corpus was readily available in this environment, and reproducing real (likely
copyrighted) veterinary textbook/journal content wouldn't be appropriate. Documented in
`ml-service/data/veterinary-reference/SOURCE.md`, consistent with `docs/DISCLAIMER.md`.

**Consequences**: the *quality* of RAG-grounded explanations is bounded by these
necessarily-brief, general summaries — not a substitute for real veterinary literature.
Swapping in a real, properly-licensed corpus later is a data-only change (re-run
`python -m app.rag.ingest` against new files) — no code changes needed, same pattern M1
established for the training dataset.

---

### 2026-09-17 — ml-service Docker builds need `apt-get` forced to HTTPS in this network

**Decision**: `ml-service/Dockerfile` now `sed`-rewrites `deb.debian.org` sources from
`http://` to `https://` before `apt-get update`.

**Why**: building the image (needed for M6's `chromadb`/`chroma-hnswlib`, which has no
`cp313` wheel — see `ml-service/AGENTS.md`) failed 3 times in a row with `apt-get install`
"Hash Sum mismatch" errors on different packages each time. The signature was diagnostic:
the *expected* hash from the Packages index was identical across all retries, but the
*received* file content differed every time — meaning something in this network path
(likely a transparent proxy or security/inspection tool) was corrupting plain-HTTP
downloads in transit, not a random flaky-network issue. Forcing HTTPS (which such tools
generally can't transparently rewrite without a trusted MITM certificate) fixed it on the
very next attempt.

**Consequences**: if this project's Docker builds are ever run on a network without this
interference, the `sed` step is a harmless no-op (HTTPS works everywhere `deb.debian.org`
does). Also separately hit, mid-diagnosis: Docker Desktop's daemon itself went fully
unresponsive (`docker ps` hanging) during the *first* build attempt — required the user to
restart Docker Desktop before builds could proceed at all. Unclear if related to the
network issue or coincidental; worth remembering as a troubleshooting step if `docker`
commands start hanging with no error.

---

### 2026-09-17 — Fixed: native pytest was fully broken by an autouse RAG-ingestion fixture

**Decision**: `tests/conftest.py`'s `_ingested_rag_knowledge_base` fixture now catches
`ImportError` and returns `None` instead of letting it propagate. `tests/test_rag_retrieval.py`
adds a module-level `pytest.importorskip("chromadb")`; the one RAG-dependent case in
`test_agent_graph.py` adds the same call inside just that test function.

**Why**: found while trying to commit M6's work — `pytest` natively errored on **all 29
tests**, not just RAG ones, because the fixture is `session`-scoped and `autouse=True`;
its `ImportError` (no `chromadb` natively) aborted session setup entirely, which pytest
treats as every test erroring. This would also have silently broken our own
`.githooks/pre-commit` for any future ml-service change. `retrieve()` itself already
degraded gracefully (verified: `run_diagnosis()` works fine without `chromadb`, just
`sources: []`) — the fixture just wasn't following the same pattern.

**Consequences**: native `pytest` now genuinely reflects this environment honestly — 24
pass, 2 skip (with a clear reason each), 0 errors. Docker still runs all 29. Any *new*
RAG-dependent test needs the same `pytest.importorskip("chromadb")` treatment, not just
"it happens to work because retrieve() degrades" — some assertions (like checking real
sources) genuinely can't be meaningful without a real Chroma collection.

---

### 2026-09-18 — Renamed `Cattle` → `Animal` + `species` field (M11), instead of deferring

**Decision**: `backend`'s `Cattle` entity/repository/service/controller/DTOs, package
(`.cattle` → `.animal`), API paths (`/api/cattle...` → `/api/animals...`), response field
(`cattleId` → `animalId`), and error codes (`CATTLE_NOT_FOUND`/`CATTLE_TAG_DUPLICATE` →
`ANIMAL_NOT_FOUND`/`ANIMAL_TAG_DUPLICATE`) all renamed in M11, plus a `species` enum field
(`COW`/`BUFFALO` today) added via a new Flyway migration
(`V2__rename_cattle_to_animal.sql` — `V1__init.sql` untouched, per `AGENTS.md`).

**Why**: 3 more species are already planned (M12–M14 — Sheep/Cat/Dog, see
`docs/ROADMAP.md`). Renaming once now costs one migration + one mechanical rename across 3
services; deferring means doing the exact same rename later anyway, after more code has
accumulated depending on the `Cattle` name, or leaving increasingly inaccurate naming in
place as non-cattle species pile onto something still called "Cattle" in the code. This was
explicitly flagged as an open question when issue #20 was created, to be resolved in M11's
spec rather than asked about twice.

**Alternatives considered**: keep the `Cattle` name and just add a `species` field —
rejected because "Cattle" stops accurately describing the table/entity the moment a second
species exists, and would read increasingly wrong through 3 more species milestones.

**Consequences**: this is a breaking API change (`/api/cattle` → `/api/animals`, `cattleId`
→ `animalId`) with no versioning ceremony — acceptable because this is a local/learning
project with no external consumers (consistent with prior deployment-scope decisions in
this log). The product's own name ("Cattle Disease Prediction System") is explicitly
**not** part of this decision — that's a separate, bigger call, out of scope for M11.

---

### 2026-09-18 — Buffalo diagnosis reuses the cattle-trained model, disclosed as an approximation (M11)

**Decision**: rather than blocking Buffalo support on a buffalo-specific dataset (none was
confirmed available — same wall M9 hit for cattle images), M11 ships a real, working Buffalo
diagnosis path that reuses the existing cattle-trained symptom model unchanged. `species` is
captured on the `Animal` record and shown in the UI, but is **not forwarded to `ml-service`**
— the request/response contract is unchanged. The frontend shows a visible disclosure
whenever a non-`COW` species is selected.

**Why**: Foot and Mouth Disease and Lumpy Skin Disease are both confirmed (via web research,
not assumed) to affect buffalo, so the existing model's predictions are a reasonable
approximation, not a wild guess — but LSD susceptibility in buffalo is documented as lower
than in cattle, a real difference this decision doesn't erase, just discloses. Mirrors the
M8 pattern: wire a real pipeline now, disclose the limitation, swap in a real model once
data exists — rather than either blocking the whole milestone or silently presenting
buffalo predictions as if a buffalo-trained model produced them.

**Consequences**: a real buffalo-specific symptom or image model is tracked as explicit
follow-up scope (not yet an issue), same status M9 was in before the Kaggle dataset was
found. Threading `species` into `ml-service`'s contract is deferred until that follow-up
has a real model to justify it — don't add the field speculatively.
`sources` content) genuinely can't be meaningful without a real Chroma collection.

---

### 2026-09-22 — Buffalo removed; Sheep gets a real, narrowly-scoped PPR model instead of the cattle-model approximation

**Decision**: `BUFFALO` is removed from `Species` (backend enum) and `SPECIES_OPTIONS`
(frontend) — not deprecated, not hidden, gone, with a Flyway migration (`V3`) cleaning up any
existing `species = 'BUFFALO'` rows. The follow-up scope the previous decision above tracked
("a real buffalo-specific model") never materialized: a second search months later still
found nothing usable. At the same time, a real, usable dataset for Sheep specifically *was*
found — [PPR disease data from goats and sheep](https://www.kaggle.com/datasets/devothanyambo/ppr-disease-data-from-goats-and-sheep)
(real field-collected clinical data, RT-qPCR-confirmed) — and `SHEEP` symptom diagnosis now
routes to `app/models/sheep_symptom_model.py`, a real trained binary PPR (Peste des Petits
Ruminants) screen (80.5% CV accuracy), replacing the cattle-model approximation Sheep used to
get on the symptom path. `species` is now forwarded to `ml-service` for symptom diagnosis
too (previously only the image path was species-aware) — the deferral in the decision above
("don't add the field speculatively... until that follow-up has a real model") is exactly
what justifies adding it now.

**Why remove Buffalo rather than leave it as a permanent approximation**: an approximation
disclosed as temporary that never gets a real replacement stops being an honest "interim"
state and just becomes a permanently wrong answer wearing a disclaimer. Two searches, months
apart, both came up empty — there's no realistic path to a real buffalo model, so the
approximation was actively removed rather than left to sit indefinitely. This is a different
call than the same situation for Buffalo's image path, or for Sheep's own foot-rot/sheep-pox
gap (still unaddressed) — those remain disclosed approximations/gaps because they're
genuinely still open follow-up scope, not because "approximation forever" is acceptable in
general.

**Why Sheep's new model is trained on combined goat+sheep data, not sheep-only**: the
dataset's `animal` column (presumably encoding goat vs. sheep) is an undocumented 0/1 value
with no data dictionary anywhere — guessing which value means which would mean silently
mislabeling real data for a diagnosis tool. PPR is the same disease in both species (same
virus, same reason the original study grouped them), so training on the full file is a
disclosed, reasoned choice, not a silent one. Full detail:
`ml-service/data/sheep-symptoms/SOURCE.md`.

**Consequences**: Sheep's symptom-diagnosis disclosure text changed from "reusing the cow
model as an approximation" to describing the model's real, narrow scope (PPR only — a
negative result means "not PPR," not "healthy"). Sheep's *image*-diagnosis path is unchanged
— still the cattle model, still a disclosed approximation, since no sheep-specific image
dataset exists either way. `PPR (Peste des Petits Ruminants)` was added to
`REPORTABLE_DISEASES` (it's WOAH/OIE-notifiable, same escalation tier as FMD/LSD).
`docs/specs/M11-buffalo-disease-detection.md` is marked superseded rather than deleted or
rewritten, per this repo's own convention of not editing history in specs; see
`docs/specs/M12-sheep-disease-detection.md`'s "Follow-up" section for the full change.

---

### 2026-09-22 — Image-mismatch detection uses a free pretrained gate, not a new trained model or species-verification (M15)

**Decision**: every image-diagnosis path (Cow/Sheep/Cat/Dog, one shared implementation) now
runs a quality gate — `app/models/species_gate.py` — before any species-specific disease
model. It uses torchvision's pretrained (zero fine-tuning) `MobileNet_V2_Weights.DEFAULT`
ImageNet-1k classifier, already a project dependency. Standard ImageNet-1k class ordering
groups every living-creature class contiguously at indices 0–397 (verified directly against
the weights' own category list, not assumed); a photo whose top-5 predictions are *all*
outside that range is rejected as `diagnosis: "invalid_image"` before reaching a disease
model at all. Deliberately **top-5, not top-1** — tested against this repo's own real
training photos first, and a real dog photo's top-1 prediction was "web site" (a total miss)
while its top-5 still included 3 correct dog breeds; top-1-only would have false-rejected a
genuinely valid photo.

**Why not a newly trained "is this species X" classifier**: would need its own dataset and
training run for a problem a free, off-the-shelf, zero-training model already solves well
enough — confirmed by testing, not assumed: real cattle/cat/dog photos all pass (3/3), real
non-animal photos (a Wikimedia table photo, a Wikimedia car photo) are both cleanly rejected
(0/5 top predictions were animal classes for either). A real finding from that same testing:
**synthetic test images (solid color, random noise, checkerboard) all incorrectly pass** —
~40% of ImageNet-1k's 1000 classes are animals, so a degenerate/uninformative image's
top-5 has a high chance of including one purely by chance. This gate is well-suited to real
accidental mismatched uploads (the actual product problem), not adversarial/synthetic input
— an acceptable, disclosed limitation for a learning project, not a security boundary.

**Why this does NOT verify the photo matches the *selected* species**: confirmed with the
user before building — the ask was "reject photos that aren't an animal at all," not "detect
a dog photo submitted while diagnosing a cat." The latter is a materially bigger, separate
problem (a prior session's `HANDOFF.md` already flagged and deferred it) and still isn't
attempted here; a wrong-species-but-real-animal photo still reaches the disease model and,
same as before this milestone, most likely comes back `"uncertain"`.

**Consequences**: `"uncertain"` and `"invalid_image"` are now two distinct, real diagnosis
values with different meanings (real animal photo, low confidence vs. not an animal at all) —
frontend code checking `diagnosis === 'uncertain'` needed auditing to make sure it wasn't
accidentally treating `invalid_image` the same way. A pre-existing bug was fixed alongside
this: the `"uncertain"` explanation text always said "not enough *symptom* information," even
for an image submission where no symptoms were ever involved — now branches on whether the
submission was image- or symptom-based. `recommended_action: "retry_upload"` is a new value
alongside the existing `escalate_to_vet`/`consult_vet`/`monitor` — the frontend renders it
with its own dedicated, non-diagnosis card style (no confidence percentage, no vet-triage
badge), not reusing the normal diagnosis-result layout. Multi-photo batches exclude
`invalid_image` results from the `diagnosesAgree` comparison (backend-side) — it isn't a
competing diagnosis to agree or disagree with the real ones in the same batch.

## Removed both databases: Postgres and Chroma (2026-09-23)

**Decision**: delete Postgres (and JPA/Flyway with it) and replace Chroma with direct reads
of the markdown reference documents. The backend is now stateless; `ml-service` keeps RAG but
retrieves from the filesystem. Spec:
[docs/specs/remove-databases.md](specs/remove-databases.md).

**Why**, measured rather than assumed, with both absent:

- Symptom diagnosis was **6/6 correct** across the disease profiles, image diagnosis **5/5**
  on real labelled photos, escalation correct for both reportable diseases, and the M15
  non-animal gate still rejected a non-animal photo. Neither database is anywhere near the
  prediction path — that's XGBoost and PyTorch reading model files.
- **Postgres was write-only**: two `save()` calls, zero queries, no history endpoint. It was
  nonetheless a hard startup dependency (Flyway failed context initialisation, so the backend
  did not boot without it), and a `save()` failure would have turned a successful diagnosis
  into a 500. Maximum coupling, no payoff.
- **Chroma was a vector index over 10.8 KB** — six documents, 40 blocks — addressed by exact
  key in both call sites: `get_precautions()` was always a metadata lookup, and `retrieve()`
  was called with a diagnosis name that `DIAGNOSIS_TO_DOC_SLUG` already maps to one document.
  It cost `chroma-hnswlib`, which has no cp313 wheel, which is why this service's tests could
  only run in Docker.

**What was explicitly given up**: diagnosis history. Nothing recorded it in a readable way
anyway. If it returns it returns with a read path, as a new spec.

**Consequences**: `ml-service`'s full suite now runs natively (79 passed, 0 skipped — it was
63 passed / 2 skipped, with the RAG file entirely skipped outside Docker). `mvn verify` needs
no database, and CI's backend job no longer provisions one. `retrieve()` is an exact lookup
rather than a similarity search, which is strictly narrower: it can no longer surface a
different disease's text. `DiagnosisCaseResponse.id` is gone — there is no row to identify,
and offering an id for something unlookupable would be a lie.
