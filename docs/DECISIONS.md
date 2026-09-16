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
