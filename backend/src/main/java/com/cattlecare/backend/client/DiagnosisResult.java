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
        @JsonProperty("next_steps") List<String> nextSteps) {
}
