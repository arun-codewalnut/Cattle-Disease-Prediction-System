# Playbook: Agentic retrospective

Closes the loop so each session makes the next one smarter — capture is automatic, the fix
is drafted, but nothing about how the agent works changes without the user approving it.

1. **Capture (already automatic)**: a `Stop` hook (`.claude/hooks/log-session-end.js`)
   appends one entry per session to `.claude/retro-logs/sessions.jsonl` (gitignored, local
   only). Nothing to do here — just don't remove the hook without a reason.
2. **Analyze**: read `.claude/retro-logs/sessions.jsonl` and recent `HANDOFF.md` history.
   Look for patterns: the same correction given more than once, repeated re-prompting on the
   same kind of task, a rule that should exist but doesn't, a skill that should have
   triggered but didn't.
3. **Draft the fix**: propose one of — a new/edited line in the relevant `AGENTS.md`, a new
   skill (or an edit to an existing skill's description/evals), or a new guardrail hook.
   Write it as a concrete diff, not a vague suggestion.
4. **Approve**: present the diff to the user and wait for a yes before applying it. Never
   edit `AGENTS.md`, a `SKILL.md`, or `.claude/settings.json` as a "silent" side effect of a
   retrospective — that's exactly the failure mode this step guards against (context bloat,
   buried rules, drift nobody agreed to).
5. **Compounds**: once approved, the fix lives in a versioned file — every future session
   inherits it automatically, same as any other `AGENTS.md`/skill change.

Don't run this reflexively every session — it's most useful after a stretch of real
implementation work, or when something visibly went wrong (repeated corrections, a wrong
guess the same way twice).
