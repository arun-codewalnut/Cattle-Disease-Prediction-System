# Roadmap

Tracked as GitHub Milestones + Issues on the repo.

- [x] **M1** — Data collection + baseline XGBoost model (`ml-service/training/`) — spec:
      [docs/specs/M1-baseline-symptom-model.md](specs/M1-baseline-symptom-model.md) — issue:
      [#1](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/1)
- [x] **M2** — FastAPI inference endpoints wrapping the model(s) — spec:
      [docs/specs/M2-wire-model-into-agent.md](specs/M2-wire-model-into-agent.md) — issue:
      [#2](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/2)
- [ ] **M3** — Spring Boot domain model + Flyway migrations + Postgres — issue:
      [#3](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/3)
- [ ] **M4** — React symptom-intake UI, calling the backend — issue:
      [#4](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/4)
- [ ] **M5** — LangGraph agent wiring: intake → route to model(s) → predict → explain — issue:
      [#5](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/5)
- [ ] **M6** — RAG knowledge base (Chroma) for grounded explanations — issue:
      [#6](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/6)
- [ ] **M7** — Notifications (email or WhatsApp Cloud API free tier) for escalation — issue:
      [#7](https://github.com/arun-codewalnut/Cattle-Disease-Prediction-System/issues/7)

**Deployment is explicitly out of scope** — this stays a local/learning project, not
something hosted for real users. Don't add a deployment milestone back without checking
with the user first (see `docs/DECISIONS.md`).

Stretch (post-MVP): image-based CNN classifier, IoT sensor anomaly detection, herd-level
risk view, offline-first mobile client.
