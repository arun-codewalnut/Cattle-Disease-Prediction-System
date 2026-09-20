package com.cattlecare.backend.diagnosis.dto;

import java.util.List;

/** Response for POST /api/animals/{animalId}/diagnoses/image — 1-5 photos in, one
 * {@link DiagnosisCaseResponse} per photo out, plus whether they all agree.
 *
 * <p>{@code diagnosesAgree} compares each photo's own model diagnosis against the others' —
 * it does NOT verify the photos are actually of the selected species (no such model exists,
 * see docs/API_CONTRACTS.md). A single photo always agrees with itself. */
public record ImageDiagnosisBatchResponse(List<DiagnosisCaseResponse> results, boolean diagnosesAgree) {

    public static ImageDiagnosisBatchResponse from(List<DiagnosisCaseResponse> results) {
        boolean agree = results.stream().map(DiagnosisCaseResponse::diagnosis).distinct().count() <= 1;
        return new ImageDiagnosisBatchResponse(results, agree);
    }
}
