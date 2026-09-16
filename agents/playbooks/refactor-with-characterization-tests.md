# Playbook: Refactoring existing code safely

Nothing in this repo needs this yet (everything is newly scaffolded) — this is the process
to use once real modules exist and accumulate the kind of tech debt every codebase does.
Don't skip straight to "rewrite this module."

1. **Characterize before touching structure.** Read the code as it exists, write a short
   behavior spec (what it actually does today, including the accidental behavior), then
   generate characterization tests from that spec — tests that pin current behavior, not
   the behavior you wish it had.
2. **Get a green baseline first.** The characterization tests must pass against the
   *current*, unrefactored code before you change a single line. If they don't pass, your
   spec is wrong — fix the spec, not the code, at this stage.
3. **Classify every behavior** you find as one of: must-preserve, intentionally-changing (and
   why), or actually-a-bug (and confirm with the user before "fixing" it as part of a
   refactor — a bugfix hiding inside a refactor PR is a review hazard).
4. **Move in small, reversible steps.** Isolate I/O from logic, split validation from side
   effects, retire one conditional branch at a time. Never one giant "rewrite this module"
   diff.
5. **Keep the suite green at every step.** Never carry a red test into the next change —
   if a change breaks a characterization test and that's intentional, that's a
   classify-first moment (step 3), not a "fix the test" moment.
6. **Preserve external contracts** unless the refactor's explicit goal is to change them:
   APIs, DB schema, logs, error shapes — see [docs/API_CONTRACTS.md](../../docs/API_CONTRACTS.md).
7. **Don't patch a test just to make the refactor pass.** If a test needs to change, that's
   a signal to go back to step 3, not a green-light to edit the assertion.

Toolkit for this repo once it applies: JUnit/pytest/Vitest (see
[docs/TESTING.md](../../docs/TESTING.md)) for the characterization tests themselves; feature
flags if a refactor needs to ship incrementally behind one.
