# Spec: Remove the optional Ollama LLM path

**Milestone**: stretch (post-M16 cleanup)
**Status**: done

## Actor + goal

A developer clones the repo, runs `pip install -r requirements.txt`, and has everything the
app uses — no optional local LLM daemon to install, configure, or wonder about.

Today the `explain` node tries Ollama (`langchain-ollama`, `LLM_PROVIDER` /
`OLLAMA_BASE_URL` / `OLLAMA_MODEL`) and falls back to a deterministic template whenever the
call fails. Ollama isn't installed or running in any environment this project uses (local
dev, CI, Docker, Railway), so **every explanation users have ever seen came from the
template**. The goal is to make that the only path and delete the unused one.

## Boundaries & failure states

- `explanation` for every diagnosis is exactly the template text it already is today —
  byte-identical, since the template function is untouched.
- `sources` on the internal `POST /agent/diagnose` response is always `[]` (it already was
  whenever the LLM wasn't used). The field stays so the internal contract doesn't change.
  The public `/api/...` endpoints never returned `sources`.
- `precautions` / `next_steps` are unchanged: they were always a deterministic lookup from
  `data/veterinary-reference/*.md` (`get_precautions()`), never LLM-generated.
- The DISCLAIMER guarantees hold as before: the template states no percentage (the result
  heading carries the one confidence figure) and invents nothing beyond the model output.

## Examples

`POST /api/diagnoses` with the four FMD symptoms → `explanation`:
"Foot and Mouth Disease is the closest match — the strongest signs were mouth lesions,
excessive salivation and lameness." (same as before this change).

## Not in scope

- LangGraph stays — it's the diagnosis pipeline (intake → predict → explain → precautions →
  recommend), not an LLM integration.
- Adding a different LLM provider. If LLM-written explanations are wanted later, that's a new
  spec (and a new dependency) — not a dormant code path kept "just in case".

## Acceptance criteria (must be checkable)

- [x] `app/agent/llm.py` is deleted; nothing imports `langchain_ollama` or `get_llm`.
- [x] `langchain-ollama` is not in `requirements.txt`; `LLM_PROVIDER`/`OLLAMA_*` are not in
      any `.env.example`.
- [x] `retrieve()` (only ever used to ground the LLM prompt) is removed; `get_precautions()`
      and its tests are unchanged.
- [x] The template-explanation tests still pass unchanged; tests that only exercised the LLM
      path are removed.
- [x] No current-state doc tells anyone to install or run Ollama.

## Agent mirror-back (fill before coding starts)

Delete the dormant LLM branch of `explain_node` and everything that only existed for it
(provider module, dependency, env vars, the retrieval call that fed the prompt, the tests of
that path). Output for every request is unchanged because the template was already the path
that ran everywhere.
