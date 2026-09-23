package com.cattlecare.backend.client;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

/** Response from ml-service's POST /agent/diagnose — see docs/API_CONTRACTS.md. */
public record DiagnosisResult(
        String diagnosis,
        double confidence,
        String explanation,
        @JsonProperty("recommended_action") String recommendedAction,
        List<String> sources,
        List<String> precautions,
        @JsonProperty("next_steps") List<String> nextSteps,
        /** Set when an uploaded photo doesn't look like the selected species — advisory,
         * the diagnosis is still returned. Null for symptom submissions and matching photos.
         * See docs/specs/species-mismatch-and-actionable-results.md. */
        @JsonProperty("species_warning") String speciesWarning) {
}
