package com.cattlecare.backend.animal.dto;

import com.cattlecare.backend.animal.Species;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record CreateAnimalRequest(@NotBlank String tagNumber, @NotNull Long farmId, @NotNull Species species) {
}
