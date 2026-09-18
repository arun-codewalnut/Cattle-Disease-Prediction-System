package com.cattlecare.backend.diagnosis.dto;

import java.time.Instant;
import java.util.List;

import com.cattlecare.backend.diagnosis.DiagnosisCase;

public record DiagnosisCaseResponse(
        Long id,
        Long animalId,
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
    public static DiagnosisCaseResponse from(
            DiagnosisCase entity, String explanation, List<String> precautions, List<String> nextSteps) {
        return new DiagnosisCaseResponse(
                entity.getId(),
                entity.getAnimalId(),
                entity.getDiagnosis(),
                entity.getConfidence(),
                explanation,
                entity.getRecommendedAction(),
                precautions,
                nextSteps,
                entity.getCreatedAt());
    }
}
