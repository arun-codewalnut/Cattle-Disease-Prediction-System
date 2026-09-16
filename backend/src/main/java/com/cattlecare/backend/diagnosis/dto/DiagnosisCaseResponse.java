package com.cattlecare.backend.diagnosis.dto;

import java.time.Instant;

import com.cattlecare.backend.diagnosis.DiagnosisCase;

public record DiagnosisCaseResponse(
        Long id,
        Long cattleId,
        String diagnosis,
        Double confidence,
        String explanation,
        String recommendedAction,
        Instant createdAt) {

    public static DiagnosisCaseResponse from(DiagnosisCase entity, String explanation) {
        return new DiagnosisCaseResponse(
                entity.getId(),
                entity.getCattleId(),
                entity.getDiagnosis(),
                entity.getConfidence(),
                explanation,
                entity.getRecommendedAction(),
                entity.getCreatedAt());
    }
}
