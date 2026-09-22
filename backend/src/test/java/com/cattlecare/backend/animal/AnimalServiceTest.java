package com.cattlecare.backend.animal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.springframework.dao.DataIntegrityViolationException;

import com.cattlecare.backend.config.ApiException;

class AnimalServiceTest {

    private final AnimalRepository animalRepository = mock(AnimalRepository.class);
    private final AnimalService animalService = new AnimalService(animalRepository);

    @Test
    void findOrCreate_newTag_savesAndReturnsAnimal() {
        when(animalRepository.findByTagNumber("COW-001")).thenReturn(Optional.empty());
        Animal saved = new Animal("COW-001", 42L, Species.COW);
        when(animalRepository.save(any())).thenReturn(saved);

        Animal result = animalService.findOrCreate("COW-001", 42L, Species.COW);

        assertEquals("COW-001", result.getTagNumber());
        assertEquals(42L, result.getFarmId());
        assertEquals(Species.COW, result.getSpecies());
    }

    @Test
    void findOrCreate_sheep_savesAndReturnsAnimalWithSheepSpecies() {
        when(animalRepository.findByTagNumber("SHE-001")).thenReturn(Optional.empty());
        Animal saved = new Animal("SHE-001", 3L, Species.SHEEP);
        when(animalRepository.save(any())).thenReturn(saved);

        Animal result = animalService.findOrCreate("SHE-001", 3L, Species.SHEEP);

        assertEquals(Species.SHEEP, result.getSpecies());
    }

    @Test
    void findOrCreate_cat_savesAndReturnsAnimalWithCatSpecies() {
        when(animalRepository.findByTagNumber("CAT-001")).thenReturn(Optional.empty());
        Animal saved = new Animal("CAT-001", 5L, Species.CAT);
        when(animalRepository.save(any())).thenReturn(saved);

        Animal result = animalService.findOrCreate("CAT-001", 5L, Species.CAT);

        assertEquals(Species.CAT, result.getSpecies());
    }

    @Test
    void findOrCreate_dog_savesAndReturnsAnimalWithDogSpecies() {
        when(animalRepository.findByTagNumber("DOG-001")).thenReturn(Optional.empty());
        Animal saved = new Animal("DOG-001", 5L, Species.DOG);
        when(animalRepository.save(any())).thenReturn(saved);

        Animal result = animalService.findOrCreate("DOG-001", 5L, Species.DOG);

        assertEquals(Species.DOG, result.getSpecies());
    }

    @Test
    void findOrCreate_raceOnInsert_throwsApiExceptionWithConflict() {
        // findByTagNumber sees nothing (not created yet), but another request wins the insert
        // race before this save() runs — same real-world conflict, just surfaced from the DB
        // constraint instead of the lookup.
        when(animalRepository.findByTagNumber("COW-001")).thenReturn(Optional.empty());
        when(animalRepository.save(any())).thenThrow(new DataIntegrityViolationException("duplicate"));

        ApiException ex = assertThrows(
                ApiException.class, () -> animalService.findOrCreate("COW-001", 42L, Species.COW));
        assertEquals("ANIMAL_TAG_DUPLICATE", ex.getCode());
    }

    // Follow-up visits: a second diagnosis for the same real animal (same tag, same farm,
    // same species) must reuse the existing record, not fail with ANIMAL_TAG_DUPLICATE —
    // that was the actual bug being fixed here.

    @Test
    void findOrCreate_existingTagSameFarmAndSpecies_reusesExistingAnimalWithoutSaving() {
        Animal existing = new Animal("COW-001", 42L, Species.COW);
        when(animalRepository.findByTagNumber("COW-001")).thenReturn(Optional.of(existing));

        Animal result = animalService.findOrCreate("COW-001", 42L, Species.COW);

        assertSame(existing, result);
        verify(animalRepository, never()).save(any());
    }

    @Test
    void findOrCreate_existingTagDifferentFarm_throwsConflictRatherThanReusing() {
        Animal existing = new Animal("COW-001", 42L, Species.COW);
        when(animalRepository.findByTagNumber("COW-001")).thenReturn(Optional.of(existing));

        ApiException ex = assertThrows(
                ApiException.class, () -> animalService.findOrCreate("COW-001", 99L, Species.COW));

        assertEquals("ANIMAL_TAG_DUPLICATE", ex.getCode());
        verify(animalRepository, never()).save(any());
    }

    @Test
    void findOrCreate_existingTagDifferentSpecies_throwsConflictRatherThanReusing() {
        Animal existing = new Animal("COW-001", 42L, Species.COW);
        when(animalRepository.findByTagNumber("COW-001")).thenReturn(Optional.of(existing));

        ApiException ex = assertThrows(
                ApiException.class, () -> animalService.findOrCreate("COW-001", 42L, Species.SHEEP));

        assertEquals("ANIMAL_TAG_DUPLICATE", ex.getCode());
        verify(animalRepository, never()).save(any());
    }

    @Test
    void getOrThrow_found_returnsAnimal() {
        Animal animal = new Animal("COW-001", 42L, Species.COW);
        when(animalRepository.findById(1L)).thenReturn(Optional.of(animal));

        assertSame(animal, animalService.getOrThrow(1L));
    }

    @Test
    void getOrThrow_notFound_throwsApiExceptionWithNotFound() {
        when(animalRepository.findById(999L)).thenReturn(Optional.empty());

        ApiException ex = assertThrows(ApiException.class, () -> animalService.getOrThrow(999L));
        assertEquals("ANIMAL_NOT_FOUND", ex.getCode());
    }
}
