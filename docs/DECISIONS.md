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
