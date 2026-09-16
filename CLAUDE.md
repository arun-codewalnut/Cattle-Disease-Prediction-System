@AGENTS.md

## Claude Code-specific notes

- Project skills live in `.claude/skills/<name>/SKILL.md`. Each is a thin adapter pointing
  at the canonical playbook in `agents/playbooks/` — edit the playbook, not the adapter,
  unless you're changing the skill's trigger/description.
- Each skill has an `evals.md` next to its `SKILL.md`: prompts that should and shouldn't
  trigger it. Update it whenever the description changes, and spot-check it occasionally.
- GitHub MCP is configured in `.mcp.json` at the repo root for issue/PR-based planning.
- Service-scoped `CLAUDE.md` files (`frontend/CLAUDE.md`, `backend/CLAUDE.md`,
  `ml-service/CLAUDE.md`) each just `@import` that service's `AGENTS.md` — keep it that way,
  don't fork content between the two files.
