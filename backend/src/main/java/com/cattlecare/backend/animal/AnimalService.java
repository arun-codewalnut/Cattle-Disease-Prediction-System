package com.cattlecare.backend.animal;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import com.cattlecare.backend.config.ApiException;

@Service
public class AnimalService {

    private final AnimalRepository animalRepository;

    public AnimalService(AnimalRepository animalRepository) {
        this.animalRepository = animalRepository;
    }

    public Animal create(String tagNumber, Long farmId, Species species) {
        try {
            return animalRepository.save(new Animal(tagNumber, farmId, species));
        } catch (DataIntegrityViolationException ex) {
            throw new ApiException(
                    "ANIMAL_TAG_DUPLICATE",
                    "An animal record with tag number '" + tagNumber + "' already exists",
                    HttpStatus.CONFLICT);
        }
    }

    /** Throws {@link ApiException} (ANIMAL_NOT_FOUND, 404) rather than returning null/Optional
     * — every caller needs the same not-found handling, so centralize it here. */
    public Animal getOrThrow(Long animalId) {
        return animalRepository.findById(animalId)
                .orElseThrow(() -> new ApiException(
                        "ANIMAL_NOT_FOUND",
                        "No animal found with id " + animalId,
                        HttpStatus.NOT_FOUND));
    }
}
