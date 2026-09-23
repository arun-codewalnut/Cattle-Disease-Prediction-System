package com.cattlecare.backend.diagnosis.dto;

import java.util.List;

/** Response for POST /api/diagnoses/image — 1-5 photos in, one
 * {@link DiagnosisCaseResponse} per photo out, plus whether they all agree.
 *
 * <p>{@code diagnosesAgree} compares each photo's own model diagnosis against the others' —
 * it does NOT verify the photos are actually of the selected species (no such model exists,
 * see docs/API_CONTRACTS.md). A single photo always agrees with itself.
 *
 * <p>M15 follow-up: {@code "invalid_image"} results (a photo that isn't of an animal at all —
 * see docs/specs/M15-image-diagnosis-quality-gate.md) are excluded from this comparison
 * entirely — it isn't a diagnosis to agree or disagree with. 4 matching real diagnoses plus 1
 * accidentally-uploaded unrelated photo should still read as "agree," not trigger the
 * disagreement warning over something that was never a competing diagnosis. */
public record ImageDiagnosisBatchResponse(List<DiagnosisCaseResponse> results, boolean diagnosesAgree) {

    // Neither of these is a diagnosis, so neither can agree or disagree with one: a photo
    // that isn't an animal, and a photo that isn't the selected species.
    private static final java.util.Set<String> NON_DIAGNOSES =
            java.util.Set.of("invalid_image", "species_mismatch");

    public static ImageDiagnosisBatchResponse from(List<DiagnosisCaseResponse> results) {
        boolean agree = results.stream()
                .map(DiagnosisCaseResponse::diagnosis)
                .filter(diagnosis -> !NON_DIAGNOSES.contains(diagnosis))
                .distinct()
                .count() <= 1;
        return new ImageDiagnosisBatchResponse(results, agree);
    }
}
