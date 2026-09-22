package com.cattlecare.backend.diagnosis.dto;

import java.util.Map;

import com.cattlecare.backend.diagnosis.Species;
import jakarta.validation.constraints.NotNull;

/** Body of POST /api/diagnoses.
 *
 * <p>{@code species} is required and deliberately has no default — it selects which trained
 * model runs in {@code ml-service}, so guessing it (e.g. defaulting to COW) would quietly
 * diagnose a sheep with the cattle model. A missing value is a VALIDATION_FAILED 400. See
 * docs/specs/remove-animal-identity.md. */
public record SubmitSymptomsRequest(@NotNull Species species, @NotNull Map<String, Object> symptoms) {
}
