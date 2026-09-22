package com.cattlecare.backend.diagnosis.dto;

import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;

import java.time.Instant;
import java.util.List;

import org.junit.jupiter.api.Test;

class ImageDiagnosisBatchResponseTest {

    private static DiagnosisCaseResponse withDiagnosis(String diagnosis) {
        return new DiagnosisCaseResponse(1L, 1L, diagnosis, 0.9, "...", "consult_vet", List.of(), List.of(), Instant.now());
    }

    // M15 (docs/specs/M15-image-diagnosis-quality-gate.md): "invalid_image" isn't a real
    // diagnosis, so it must never count toward — or against — agreement between the others.

    @Test
    void allInvalidImages_stillCountsAsAgreeing() {
        var response = ImageDiagnosisBatchResponse.from(List.of(
                withDiagnosis("invalid_image"), withDiagnosis("invalid_image")));

        assertTrue(response.diagnosesAgree());
    }

    @Test
    void oneInvalidImagePlusOneRealDiagnosis_stillAgrees() {
        var response = ImageDiagnosisBatchResponse.from(List.of(
                withDiagnosis("Ringworm"), withDiagnosis("invalid_image")));

        assertTrue(response.diagnosesAgree());
    }

    @Test
    void invalidImagePlusTwoDisagreeingRealDiagnoses_stillFlagsDisagreement() {
        var response = ImageDiagnosisBatchResponse.from(List.of(
                withDiagnosis("Ringworm"), withDiagnosis("Scabies"), withDiagnosis("invalid_image")));

        assertFalse(response.diagnosesAgree());
    }
}
