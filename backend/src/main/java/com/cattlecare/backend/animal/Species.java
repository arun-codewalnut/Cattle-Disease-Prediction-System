package com.cattlecare.backend.animal;

/** Which species an {@link Animal} record is for. Grows one milestone at a time — never
 * reorder existing values, since this is mapped by name ({@code EnumType.STRING}), not
 * ordinal, but a reorder would still be a needless diff against every future PR touching
 * this enum.
 *
 * <p>{@code BUFFALO} (M11) was removed as a supported species — see
 * docs/specs/M11-buffalo-disease-detection.md's "Superseded" note: no usable buffalo
 * symptom or image dataset was ever found, so it never moved past a disclosed
 * cow-model approximation. Dropped rather than left half-supported.
 *
 * <p>Not every species here supports diagnosis yet — see
 * {@link com.cattlecare.backend.diagnosis.DiagnosisService#DIAGNOSIS_SUPPORTED_SPECIES}.
 * Cat (M13) and Dog (M14) are recorded but diagnosis is deliberately blocked for both: the
 * cattle-trained model's disease list and symptom vocabulary don't apply to a companion
 * animal at all, unlike Sheep, where a real sheep/goat-trained model exists (M12 follow-up)
 * for symptom diagnosis specifically. See docs/specs/M13-cat-disease-detection.md and
 * docs/specs/M14-dog-disease-detection.md. */
public enum Species {
    COW,
    SHEEP,
    CAT,
    DOG,
}
