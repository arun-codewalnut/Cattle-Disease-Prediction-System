# Disclaimer

This system is a **learning project**, not a certified veterinary diagnostic tool.

- Predictions are probabilistic model output, not a medical diagnosis. Always present
  results as "likely X, confidence Y%" — never as a definitive diagnosis.
- For any output matching a reportable/contagious disease (e.g. Foot and Mouth Disease,
  Lumpy Skin Disease), the agent must always recommend veterinary/authority verification,
  regardless of model confidence — never auto-resolve a case as "handled."
- Do not use this system's output as the sole basis for a real animal-health or
  herd-management decision.

Any feature that adds real-world action (notifications, escalation, reporting to an
authority) must preserve this behavior. See
[docs/API_CONTRACTS.md](API_CONTRACTS.md) for the `recommended_action` field this maps to.
