package com.cattlecare.backend.animal;

import java.util.Optional;

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

    /** Find-or-create by tag number, so a follow-up diagnosis for the same real animal (e.g.
     * "COW-001" again 2 months later) attaches to its existing history instead of permanently
     * failing with ANIMAL_TAG_DUPLICATE — every diagnosis submission calls this, not create()
     * directly, so repeat visits just work without any extra "look up my animal" step in the
     * UI. tag_number stays globally unique (V1__init.sql), so the lookup is by tag alone.
     *
     * <p>If the tag exists but farmId or species don't match what's now being submitted,
     * that's treated as a real conflict (most likely a typo'd tag reused for a different
     * animal), not a legitimate revisit — still rejected with ANIMAL_TAG_DUPLICATE rather than
     * silently overwriting the existing record's species/farm, which would corrupt its
     * history. */
    public Animal findOrCreate(String tagNumber, Long farmId, Species species) {
        Optional<Animal> existing = animalRepository.findByTagNumber(tagNumber);
        if (existing.isPresent()) {
            Animal animal = existing.get();
            if (!animal.getFarmId().equals(farmId) || animal.getSpecies() != species) {
                throw new ApiException(
                        "ANIMAL_TAG_DUPLICATE",
                        "An animal record with tag number '" + tagNumber
                                + "' already exists for a different farm or species.",
                        HttpStatus.CONFLICT);
            }
            return animal;
        }

        try {
            return animalRepository.save(new Animal(tagNumber, farmId, species));
        } catch (DataIntegrityViolationException ex) {
            // Race: another request created this exact tag between findByTagNumber above and
            // this save — same conflict, just surfaced from the DB constraint instead.
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
