package com.cattlecare.backend.diagnosis.dto;

import java.time.Instant;
import java.util.List;

import com.cattlecare.backend.client.DiagnosisResult;
import com.cattlecare.backend.diagnosis.Species;

/** One diagnosis, returned straight from ml-service's result.
 *
 * <p>Nothing is persisted any more (docs/specs/remove-databases.md), so this is built from
 * the live result rather than a saved row. The old {@code id} is gone with the row it
 * identified — offering an id for something that can't be looked up would be a lie. Tracing
 * a request across services is the correlation ID's job, as it always was. {@code createdAt}
 * stays: it's generated here and still says when the diagnosis was made. */
public record DiagnosisCaseResponse(
        Species species,
        String diagnosis,
        Double confidence,
        String explanation,
        String recommendedAction,
        List<String> precautions,
        List<String> nextSteps,
        Instant createdAt) {

    public static DiagnosisCaseResponse from(Species species, DiagnosisResult result) {
        return new DiagnosisCaseResponse(
                species,
                result.diagnosis(),
                result.confidence(),
                result.explanation(),
                result.recommendedAction(),
                result.precautions(),
                result.nextSteps(),
                Instant.now());
    }
}
