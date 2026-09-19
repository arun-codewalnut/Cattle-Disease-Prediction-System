package com.cattlecare.backend.animal.dto;

import java.time.Instant;

import com.cattlecare.backend.animal.Animal;
import com.cattlecare.backend.animal.Species;

public record AnimalResponse(Long id, String tagNumber, Long farmId, Species species, Instant createdAt) {

    public static AnimalResponse from(Animal animal) {
        return new AnimalResponse(
                animal.getId(), animal.getTagNumber(), animal.getFarmId(), animal.getSpecies(), animal.getCreatedAt());
    }
}
