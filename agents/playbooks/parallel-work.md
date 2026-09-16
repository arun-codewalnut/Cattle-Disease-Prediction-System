# Playbook: Running independent milestones in parallel

Only worth doing when tasks genuinely don't touch the same files — e.g. M4 (React UI) and
M7 (notifications) barely overlap; M1 and M2 do (M2 depends on M1's model existing) and
should stay sequential.

## Setup — one worktree + branch per independent task

```bash
git worktree add ../Client-Project-wt-<short-name> -b <type>/<short-name>
```

Example, running the React UI (M4) and the notification integration (M7) in parallel:

```bash
git worktree add ../Client-Project-wt-symptom-ui -b feat/symptom-intake-ui
git worktree add ../Client-Project-wt-notifications -b feat/notification-integration
```

Each worktree is a full, independent checkout — open a separate agent session (or Claude
Code instance) per worktree, pointed at that directory. Don't run two agents against the
same working directory on overlapping files; that's what worktrees prevent.

## Rules

- One task, one worktree, one branch, one PR. Don't let a "quick fix" in a parallel
  worktree touch files outside that task's scope.
- Review each PR independently before merging — treat parallel-agent output exactly like a
  PR from a teammate you haven't met, per [CONTRIBUTING.md](../../CONTRIBUTING.md).
- Merge one at a time, not all at once — resolve any cross-branch conflicts (e.g. both
  touching `docs/API_CONTRACTS.md`) deliberately, not by force-pushing over one.
- Clean up finished worktrees: `git worktree remove ../Client-Project-wt-<short-name>`.

## For one complex task instead (not independent parallel tasks)

Use subagents from a single main thread: one focused search/research/check per subagent,
each returning a tight summary. The main thread keeps the plan and writes the final diff —
subagents don't edit code directly. This is the right tool when a task is complex but not
actually separable (e.g. "investigate why correlation IDs aren't showing up in ml-service
logs" — one investigation, several angles, not several independent deliverables).
