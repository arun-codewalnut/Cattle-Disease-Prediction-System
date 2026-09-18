# Roadmap

Tracked as GitHub Milestones + Issues on the repo.

- [x] **M1** — Data collection + baseline XGBoost model (`ml-service/training/`) — spec:
      [docs/specs/M1-baseline-symptom-model.md](specs/M1-baseline-symptom-model.md) — issue:
      [#1](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/1)
- [x] **M2** — FastAPI inference endpoints wrapping the model(s) — spec:
      [docs/specs/M2-wire-model-into-agent.md](specs/M2-wire-model-into-agent.md) — issue:
      [#2](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/2)
- [x] **M3** — Spring Boot domain model + Flyway migrations + Postgres — spec:
      [docs/specs/M3-backend-domain-model.md](specs/M3-backend-domain-model.md) — issue:
      [#3](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/3)
- [x] **M4** — React symptom-intake UI, calling the backend — spec:
      [docs/specs/M4-symptom-intake-ui.md](specs/M4-symptom-intake-ui.md) — issue:
      [#4](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/4)
- [x] **M5** — LangGraph agent wiring: intake → route to model(s) → predict → explain — spec:
      [docs/specs/M5-langgraph-agent-orchestration.md](specs/M5-langgraph-agent-orchestration.md) — issue:
      [#5](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/5)
- [x] **M6** — RAG knowledge base (Chroma) for grounded explanations — spec:
      [docs/specs/M6-rag-knowledge-base.md](specs/M6-rag-knowledge-base.md) — issue:
      [#6](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/6)
- [ ] **M7** — Notifications (email or WhatsApp Cloud API free tier) for escalation — issue:
      [#7](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/7)
- [ ] **M8** — Image-based disease recognition, phase 1: wire upload → agent's
      `predict_image` node end-to-end behind a placeholder classifier (no dataset/training
      yet — that's M9) — issue:
      [#16](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/16)
- [ ] **M9** — Train a real cattle image classifier (Healthy/LSD/FMD), replacing M8's
      byte-hash placeholder — issue:
      [#18](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/18)
- [ ] **M10** — Diagnosis precautions and next-steps, RAG-grounded (species-agnostic,
      applies to the existing cattle flow immediately) — issue:
      [#19](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/19)
- [ ] **M11** — Buffalo disease detection — first new species; generalizes the domain model
      to support animal type — issue:
      [#20](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/20)
- [ ] **M12** — Sheep disease detection — issue:
      [#21](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/21)
- [ ] **M13** — Cat disease detection — first companion-animal species, a real domain pivot
      from livestock — issue:
      [#22](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/22)
- [ ] **M14** — Dog disease detection — issue:
      [#23](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/23)

**Deployment is explicitly out of scope** — this stays a local/learning project, not
something hosted for real users. Don't add a deployment milestone back without checking
with the user first (see `docs/DECISIONS.md`).

Also tracked (not milestone-numbered): frontend UI redesign (cattle-themed, responsive,
colorful, icon-driven) — issue:
[#15](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/15).

**Target species** (per user request, 2026-09-18): Cow (done), Buffalo, Sheep, Cat, Dog —
sequenced M11→M14 above. M11 is where the domain model first generalizes beyond cattle; see
that issue's "open design question" before assuming the shape of anything downstream.

Stretch (post-MVP): IoT sensor anomaly detection, herd-level risk view, offline-first mobile
client.
