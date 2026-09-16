## Summary

<!-- What changed and why. Link the issue/milestone: Closes #___ / Relates to M__ -->

## Affected service(s)

- [ ] frontend
- [ ] backend
- [ ] ml-service
- [ ] docs / infra / cross-service

## Checklist

- [ ] Tests pass for the affected service(s)
- [ ] `docs/API_CONTRACTS.md` updated if the request/response shape changed
- [ ] `STATE.md` / `HANDOFF.md` updated if this is a meaningful chunk of work
- [ ] If this touches diagnosis/escalation logic: reviewed against
      [docs/DISCLAIMER.md](../docs/DISCLAIMER.md) — no auto-resolving of reportable-disease
      cases, confidence always surfaced, not overstated as a definitive diagnosis
- [ ] No real secrets committed (`.env` files, API keys)

## How was this tested?

<!-- e.g. mvn test / pytest / npm run lint / manual make up + click-through -->
