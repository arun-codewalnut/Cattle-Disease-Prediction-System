# Contributing

This is a solo learning project developed with agentic-AI assistance (Claude Code + GitHub
MCP), but it follows normal issue/PR discipline so that workflow stays legible.

## One-time setup

```bash
git config core.hooksPath .githooks
```

This enables the pre-commit hook (`.githooks/pre-commit`) — the first rung of the evidence
ladder: it lints/compiles/tests only the service(s) you actually changed, before the commit
lands. It's local config (per clone), not tracked by git itself, so every fresh clone needs
to run this once.

## Workflow

1. Work is tracked as GitHub issues, grouped under the milestones in
   [docs/ROADMAP.md](docs/ROADMAP.md) (M1–M8).
2. Branch per issue/task: `<type>/<short-description>` — e.g. `feat/xgboost-baseline-model`,
   `fix/correlation-id-not-forwarded`, `docs/update-api-contract`.
3. Commit messages: small, focused, imperative mood (`Add Flyway migration for cattle table`,
   not `Added stuff`). Reference the issue number when one exists (`Fixes #12`).
4. Open a PR against `main` using the PR template — it's filled in automatically.
5. **Before merging, run `/code-review` on the diff** — even for solo-authored PRs. Read it
   yourself too: your name is on the commit. The review should cover, at minimum:
   correctness (bugs, edge cases), NFRs (security, performance, accessibility where
   relevant), test quality (tests prove behavior, not implementation), and code quality
   (naming, duplication, convention adherence). Triage findings — fix, defer with a reason,
   or dismiss with a reason — don't merge with unaddressed high-severity findings.
6. Confirm: relevant service's tests pass, `docs/API_CONTRACTS.md` is updated if the
   contract changed, and [STATE.md](STATE.md)/[HANDOFF.md](HANDOFF.md) reflect the change if
   it's a meaningful chunk of work (see [AGENTS.md](AGENTS.md) for what "meaningful" means
   here).

## Conventions

Full conventions live in [AGENTS.md](AGENTS.md) (cross-cutting) and each service's own
`AGENTS.md` (stack-specific). Read the relevant one before making changes.

## Safety

This project touches animal-health predictions — read
[docs/DISCLAIMER.md](docs/DISCLAIMER.md) before changing anything in the diagnosis/escalation
path.
