# Evals: run-stack

Manual trigger check — run these against a fresh session and confirm the skill fires (or
doesn't) as expected. Re-check after editing `SKILL.md`'s description.

## Should trigger

- "start the app"
- "boot up the stack locally"
- "how do I preview the frontend"
- "run just the ml-service"

## Should NOT trigger

- "what does the ml-service do" (informational, not a run request — should just answer
  from `ml-service/AGENTS.md`, not invoke this skill)
- "deploy this to production" (different concern — deployment, not local run)
