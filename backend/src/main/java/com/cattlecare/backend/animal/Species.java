package com.cattlecare.backend.animal;

/** Which species an {@link Animal} record is for. Grows one milestone at a time — see
 * docs/ROADMAP.md M14 (Dog) — never reorder existing values, since this is mapped by name
 * ({@code EnumType.STRING}), not ordinal, but a reorder would still be a needless diff
 * against every future PR touching this enum.
 *
 * <p>Not every species here supports diagnosis yet — see
 * {@link com.cattlecare.backend.diagnosis.DiagnosisService#DIAGNOSIS_SUPPORTED_SPECIES}.
 * Cat (M13) is recorded but diagnosis is deliberately blocked: the cattle-trained model's
 * disease list and symptom vocabulary don't apply to a cat at all, unlike the livestock
 * species above it, where reusing that model is a disclosed approximation rather than a
 * wrong-species result. See docs/specs/M13-cat-disease-detection.md. */
public enum Species {
    COW,
    BUFFALO,
    SHEEP,
    CAT,
}
