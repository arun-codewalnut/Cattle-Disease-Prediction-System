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
- **Dog's image model was retrained (M16 follow-up)** on a new skin-disease dataset: 70.5%
  validation accuracy, 0.683 macro F1, across Bacterial Dermatosis, Fungal Infection, Healthy,
  and Hypersensitivity/Allergic Dermatosis — a substantial improvement over the original
  52.6%/no-Healthy-class model. Bacterial Dermatosis is still the weakest class (0.52 F1) —
  wrong more often than the others, though far above the old model's worst class (0.25 F1).
  **It now has a real Healthy class** (0.78 F1, the strongest one).

The rest of this document's guarantees (probabilistic estimate, not a diagnosis; never the
sole basis for a real decision) apply identically regardless of audience — a pet owner needs
the same honesty a farmer/vet does, just framed for a different context and different stakes
(an individual companion animal, not herd economics). That honesty is exactly what makes
per-class accuracy caveats like Dog's non-negotiable to state clearly, not just technically
true somewhere.

## Goat (M16)

Goat has a real, trained image model — but a **binary** one: `Healthy` or `Unhealthy`, 80.1%
validation accuracy. No disease-specific goat image dataset was found anywhere in this
session's search, so **the model can flag that a goat photo looks off, but it can never say
what's wrong**. An `Unhealthy` result gets generic guidance (isolate the animal, consult a
vet, take a closer photo of the area of concern) rather than disease-specific precautions,
because there is no specific disease identified. Goat has no symptom model either — the
closest candidate data (the PPR dataset Sheep's symptom model uses) can't be reliably split
by species (see `ml-service/data/sheep-symptoms/SOURCE.md`), so symptom-based diagnosis stays
blocked for Goat, same as Cat and Dog.

**A real, measured side effect of the Dog dataset swap above, unrelated to Goat itself**: the
species-mismatch detector (which flags a dog photo submitted with Cow selected, etc.) got
measurably weaker at catching dog-as-cow specifically — from ~80% to ~30% caught on 40-photo
samples — because Dog's new disease dataset is skin-lesion close-ups, which don't show the
face/ears/snout features the detector's underlying model keys on. This was judged an
acceptable tradeoff for the real accuracy gain on Dog's actual diagnosis, but it is a real,
disclosed change in how well that unrelated safety guard performs specifically for dog
photos — see `docs/specs/M16-goat-disease-detection.md` and `docs/DECISIONS.md` for the full
measurement.
