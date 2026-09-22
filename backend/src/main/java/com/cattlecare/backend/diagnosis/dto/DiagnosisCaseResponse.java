package com.cattlecare.backend.diagnosis.dto;

import java.time.Instant;
import java.util.List;

import com.cattlecare.backend.diagnosis.DiagnosisCase;
import com.cattlecare.backend.diagnosis.Species;

public record DiagnosisCaseResponse(
        Long id,
        Species species,
        String diagnosis,
        Double confidence,
        String explanation,
        String recommendedAction,
        List<String> precautions,
        List<String> nextSteps,
        Instant createdAt) {

    // precautions/nextSteps are, like explanation, returned live from ml-service and never
    // persisted (docs/specs/M10-precautions-next-steps.md — same precedent as explanation,
    // see docs/API_CONTRACTS.md).
    //
    // `species` replaced `animalId` here when animal identity was removed — see
    // docs/specs/remove-animal-identity.md.
    public static DiagnosisCaseResponse from(
            DiagnosisCase entity, String explanation, List<String> precautions, List<String> nextSteps) {
        return new DiagnosisCaseResponse(
                entity.getId(),
                entity.getSpecies(),
                entity.getDiagnosis(),
                entity.getConfidence(),
                explanation,
                entity.getRecommendedAction(),
                precautions,
                nextSteps,
                entity.getCreatedAt());
    }
}
