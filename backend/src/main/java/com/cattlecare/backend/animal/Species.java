package com.cattlecare.backend.animal;

/** Which species an {@link Animal} record is for. Grows one milestone at a time — see
 * docs/ROADMAP.md M13-M14 (Cat, Dog) — never reorder existing values, since this is
 * mapped by name ({@code EnumType.STRING}), not ordinal, but a reorder would still be a
 * needless diff against every future PR touching this enum. */
public enum Species {
    COW,
    BUFFALO,
    SHEEP,
}
