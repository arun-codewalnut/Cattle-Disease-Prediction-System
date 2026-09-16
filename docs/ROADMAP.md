# Roadmap

Mirror these as GitHub issues/milestones once GitHub MCP is connected (see
[agents/playbooks/](../agents/playbooks/) and `HANDOFF.md`).

- [ ] **M1** — Data collection + baseline XGBoost model (`ml-service/training/`) — spec:
      [docs/specs/M1-baseline-symptom-model.md](specs/M1-baseline-symptom-model.md)
- [ ] **M2** — FastAPI inference endpoints wrapping the model(s)
- [ ] **M3** — Spring Boot domain model + Flyway migrations + Postgres
- [ ] **M4** — React symptom-intake UI, calling the backend
- [ ] **M5** — LangGraph agent wiring: intake → route to model(s) → predict → explain
- [ ] **M6** — RAG knowledge base (Chroma) for grounded explanations
- [ ] **M7** — Notifications (email or WhatsApp Cloud API free tier) for escalation
- [ ] **M8** — Deployment on free-tier hosting (Render/Railway + Vercel + Supabase)

Stretch (post-MVP): image-based CNN classifier, IoT sensor anomaly detection, herd-level
risk view, offline-first mobile client.
