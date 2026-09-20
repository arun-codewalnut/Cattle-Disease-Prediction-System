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

**Cat and Dog now have real, trained IMAGE diagnosis models** (M13/M14 follow-up) —
`docs/specs/M13-cat-disease-detection.md` and `M14-dog-disease-detection.md`'s "Follow-up"
sections have the full detail. **Rabies escalation is still not implemented as code** —
neither trained model has a Rabies class (no rabies image data exists), so there is nothing
for an escalation rule to attach to yet. This is the same "not yet" this document already
said, unchanged by a real model now existing for other diseases.

**SYMPTOM-based diagnosis stays deliberately blocked for Cat/Dog**
(`DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES`) — no symptom model or data exists for either, and
reusing the cattle-trained symptom model's output for a cat or dog would present a livestock
disease as if it were a real finding for a companion animal, which is worse than no answer
at all.

**Real accuracy, stated plainly, not softened**:
- **Cat's image model is solid**: 83.0% validation accuracy across Flea Allergy, Healthy,
  Ringworm, Scabies.
- **Dog's image model is real but meaningfully weak**: 52.6% validation accuracy, and only
  0.25 F1 for Canine Distemper specifically — wrong more often than right for that disease.
  Mange is the one class it's actually decent at (0.75 F1). **It has no Healthy class at
  all** — a Dog image diagnosis always names one of Canine Distemper, Canine Parvovirus,
  Kennel Cough, or Mange, even for a perfectly healthy dog. Shipped anyway, per an explicit
  decision to disclose loudly rather than withhold — the frontend states this before a photo
  is even uploaded, not just here.

The rest of this document's guarantees (probabilistic estimate, not a diagnosis; never the
sole basis for a real decision) apply identically regardless of audience — a pet owner needs
the same honesty a farmer/vet does, just framed for a different context and different stakes
(an individual companion animal, not herd economics). That honesty is exactly what makes the
Dog caveat above non-negotiable to state clearly, not just technically true somewhere.
