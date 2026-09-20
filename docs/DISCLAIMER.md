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

**Image-based prediction (M9)** covers only 3 of the 5 symptom-model diseases — `Healthy`,
`Lumpy Skin Disease`, `Foot and Mouth Disease` — since no image dataset exists for
`Mastitis`/`Bovine Respiratory Disease`. Don't present an image-based diagnosis as having the
same disease coverage as a symptom-based one.

## Companion animals (M13+)

This project started as livestock-only (cattle/buffalo/sheep), where "reportable disease"
means economically significant, herd-level contagious diseases (Foot and Mouth Disease,
Lumpy Skin Disease) that animal-health authorities require reporting. Companion animals
(cat, dog) carry a different equivalent: **rabies**. Veterinarians are under a legal
mandatory-reporting obligation for suspected or confirmed rabies in cats and dogs to local
public-health authorities — a real, non-optional equivalent to `REPORTABLE_DISEASES`, with
even higher stakes (rabies is a fatal zoonotic disease).

**Whenever a real companion-animal diagnosis model is built** (none exists yet — see
`docs/specs/M13-cat-disease-detection.md`), rabies/suspected rabies exposure must be added
to a companion-animal equivalent of `REPORTABLE_DISEASES` from the first version of that
model, not retrofitted after. Until then, diagnosis is deliberately blocked entirely for
species without a real model (`DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`) — reusing the
cattle-trained model's output for a cat or dog would present a livestock disease as if it
were a real finding for a companion animal, which is worse than no answer at all.

The rest of this document's guarantees (probabilistic estimate, not a diagnosis; never the
sole basis for a real decision) apply identically regardless of audience — a pet owner needs
the same honesty a farmer/vet does, just framed for a different context and different stakes
(an individual companion animal, not herd economics).
