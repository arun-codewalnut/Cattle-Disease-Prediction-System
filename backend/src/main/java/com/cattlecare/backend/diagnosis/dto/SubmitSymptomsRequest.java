package com.cattlecare.backend.diagnosis.dto;

import java.util.Map;

import jakarta.validation.constraints.NotNull;

public record SubmitSymptomsRequest(@NotNull Map<String, Object> symptoms) {
}
