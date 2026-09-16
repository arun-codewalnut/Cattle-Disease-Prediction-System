package com.cattlecare.backend.cattle.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record CreateCattleRequest(@NotBlank String tagNumber, @NotNull Long farmId) {
}
