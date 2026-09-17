# Spec: LangGraph agent orchestration

**Milestone**: M5
**Status**: done

## Actor + goal

`run_diagnosis()` (called from `POST /agent/diagnose`, unchanged external contract) is
restructured from one plain function into an explicit LangGraph `StateGraph` — distinct
`intake`, `route`, `predict_symptoms`/`predict_image`, `explain`, `recommend` nodes — and
the `explain` node starts generating real LLM text instead of a fixed template.

**What this milestone changes and doesn't change** (see the conversation in `HANDOFF.md` —
worth stating explicitly since it's an easy thing to overclaim):
- Changes: how the explanation text is produced (LLM-generated, grounded in the model's
  actual output), and the code structure (explicit graph vs. one function).
- Does NOT change: the diagnosis, confidence, or top_features — still 100% the M1 XGBoost
  model, untouched. Does NOT change `recommended_action` logic — still the hardcoded
  `REPORTABLE_DISEASES` safety rule from M2, not delegated to the LLM.

## Boundaries & failure states

- **The LLM must be swappable (local or remote) without touching graph logic.** `app/agent/llm.py`
  reads `LLM_PROVIDER` (from `ml-service/.env.example`, defaults to `ollama`) and returns a
  LangChain chat model instance — the `explain` node calls it through that one abstraction,
  never instantiates a provider directly.
- **The LLM is not on the critical path for safety-relevant output.** If the LLM call fails
  for any reason (Ollama not running, timeout, malformed response), `explain` falls back to
  the same deterministic template M2 already had — the diagnosis and recommended action are
  never blocked by an LLM being unavailable. A diagnosis tool cannot go down because a local
  LLM daemon isn't running.
- **The LLM must not invent medical facts.** The prompt explicitly constrains it to the
  diagnosis, confidence, and top contributing features already computed — it explains
  *given* data, it doesn't generate new claims. (This is what "grounded" means here; full
  RAG-sourced grounding is M6, not this milestone.)
- **`recommended_action` is still computed by the hardcoded rule, after `explain`, not by
  the LLM** — the `recommend` node doesn't read the LLM's output at all.
- **`image_url` provided → routes to a `predict_image` node that returns a clear
  `NOT_IMPLEMENTED` error (`501`)**, not silent ignoring (M2's behavior) and not a crash.
  Real image-based prediction is a separate, later milestone — this just makes the
  routing structure real and the current limitation explicit to the caller.

## Examples

**Input** (unchanged from M2): `POST /agent/diagnose` with `{"symptoms": {...}}`.

**Successful response** (shape unchanged from `docs/API_CONTRACTS.md` — only `explanation`'s
*content* differs, now LLM-generated instead of templated):
```json
{
  "diagnosis": "Foot and Mouth Disease",
  "confidence": 0.81,
  "explanation": "Based on the fever, mouth lesions, and excessive salivation observed, this points strongly toward Foot and Mouth Disease...",
  "recommended_action": "escalate_to_vet",
  "sources": []
}
```

**Edge case — Ollama not running**: same response shape, `explanation` falls back to M2's
template text (`"Predicted X with Y% confidence, based primarily on: ..."`) — the caller
gets no error, no degraded diagnosis, just the older-style explanation text.

**Edge case — `image_url` provided**: `501` `{"code": "NOT_IMPLEMENTED", "message": "Image-based prediction isn't implemented yet.", "details": null}`.

## Not in scope

- Real image-based prediction (the `predict_image` node is a clear stub, not a real model).
- RAG-grounded explanations (M6) — the LLM prompt is constrained to the model's own output,
  not retrieved documents.
- Any change to `recommended_action` logic, the XGBoost model, or the API's external
  request/response contract.

## Acceptance criteria

- [x] `app/agent/graph.py` defines an explicit LangGraph `StateGraph` with `intake`,
      `route`, `predict_symptoms`, `predict_image`, `explain`, `recommend` nodes.
- [x] `app/agent/llm.py` provides one `get_llm()` abstraction reading `LLM_PROVIDER`;
      `explain` node calls only through this — never instantiates `ChatOllama` (or any
      provider) directly.
- [x] `explain` node: successful LLM call → LLM-generated text grounded in
      diagnosis/confidence/top_features; failed LLM call (any exception) → falls back to
      M2's deterministic template, no error surfaced to the caller.
- [x] `image_url` present → routes to `predict_image` → raises `ApiError("NOT_IMPLEMENTED", ..., 501)`.
- [x] `recommend` node unchanged behavior from M2: reportable diseases always
      `escalate_to_vet` regardless of confidence; `"uncertain"` always `consult_vet`;
      `"Healthy"` → `monitor`.
- [x] `run_diagnosis()`'s external signature and return shape are unchanged — `app/api/diagnose.py`
      required no changes.
- [x] Tests cover: LLM-success path (mocked LLM), LLM-failure fallback path (mocked to
      raise), the image-not-implemented path, and that `recommended_action`/escalation
      behavior from M2's tests still holds — none require a real running Ollama instance.
      (`tests/test_agent_graph.py`, 6 new tests, all passing.)
- [x] `ml-service/tests/test_diagnose_endpoint.py` (M2's suite) still passes unchanged —
      21/21 total, all green. (Confirmed Ollama genuinely isn't installed in this
      environment — `where ollama` found nothing — so the fallback path exercised by these
      tests reflects real local conditions, not a hypothetical.)

## Agent mirror-back

**Intent**: restructure the diagnosis flow into an explicit, auditable LangGraph graph, and
make the explanation LLM-generated (provider-swappable, local or remote) while keeping
every safety-relevant decision (which disease, how confident, whether to escalate) exactly
as deterministic as it already was. The graph adds structure and better explanations, not
new judgment.

**Inputs/outputs**: unchanged from M2's `run_diagnosis()` — same call signature, same
response shape. This milestone is entirely internal restructuring plus one new
observable-but-non-critical behavior (LLM-generated explanation text).

**Assumptions flagged before coding**:
1. **New dependency**: `langchain-ollama==0.2.2` (compatible with the already-pinned
   `langchain-core==0.3.28` — verified via PyPI metadata; newer `langchain-ollama` releases
   need `langchain-core>=0.3.33`/`>=1.2` and would force an unplanned upgrade).
2. **No real Ollama instance is assumed to be running** in this environment. All automated
   tests mock the LLM layer (`get_llm()`) — nothing here depends on Ollama actually being
   installed. If Ollama happens to be available, a live end-to-end check is a bonus, not a
   requirement for "done."
3. **The fallback-on-any-exception in `explain`** is deliberately broad (bare `except
   Exception`, not specific exception types) — an LLM call can fail in many
   provider-specific ways (connection refused, timeout, malformed response, rate limit for
   a remote provider later), and all of them should degrade the same way: fall back, never
   crash the diagnosis.
