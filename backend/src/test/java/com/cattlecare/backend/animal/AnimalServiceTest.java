package com.cattlecare.backend.animal;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.springframework.dao.DataIntegrityViolationException;

import com.cattlecare.backend.config.ApiException;

class AnimalServiceTest {

    private final AnimalRepository animalRepository = mock(AnimalRepository.class);
    private final AnimalService animalService = new AnimalService(animalRepository);

    @Test
    void create_savesAndReturnsAnimal() {
        Animal saved = new Animal("COW-001", 42L, Species.COW);
        when(animalRepository.save(any())).thenReturn(saved);

        Animal result = animalService.create("COW-001", 42L, Species.COW);

        assertEquals("COW-001", result.getTagNumber());
        assertEquals(42L, result.getFarmId());
        assertEquals(Species.COW, result.getSpecies());
    }

    @Test
    void create_buffalo_savesAndReturnsAnimalWithBuffaloSpecies() {
        Animal saved = new Animal("BUF-001", 7L, Species.BUFFALO);
        when(animalRepository.save(any())).thenReturn(saved);

        Animal result = animalService.create("BUF-001", 7L, Species.BUFFALO);

        assertEquals(Species.BUFFALO, result.getSpecies());
    }

    @Test
    void create_sheep_savesAndReturnsAnimalWithSheepSpecies() {
        Animal saved = new Animal("SHE-001", 3L, Species.SHEEP);
        when(animalRepository.save(any())).thenReturn(saved);

        Animal result = animalService.create("SHE-001", 3L, Species.SHEEP);

        assertEquals(Species.SHEEP, result.getSpecies());
    }

    @Test
    void create_cat_savesAndReturnsAnimalWithCatSpecies() {
        Animal saved = new Animal("CAT-001", 5L, Species.CAT);
        when(animalRepository.save(any())).thenReturn(saved);

        Animal result = animalService.create("CAT-001", 5L, Species.CAT);

        assertEquals(Species.CAT, result.getSpecies());
    }

    @Test
    void create_dog_savesAndReturnsAnimalWithDogSpecies() {
        Animal saved = new Animal("DOG-001", 5L, Species.DOG);
        when(animalRepository.save(any())).thenReturn(saved);

        Animal result = animalService.create("DOG-001", 5L, Species.DOG);

        assertEquals(Species.DOG, result.getSpecies());
    }

    @Test
    void create_duplicateTag_throwsApiExceptionWithConflict() {
        when(animalRepository.save(any())).thenThrow(new DataIntegrityViolationException("duplicate"));

        ApiException ex = assertThrows(
                ApiException.class, () -> animalService.create("COW-001", 42L, Species.COW));
        assertEquals("ANIMAL_TAG_DUPLICATE", ex.getCode());
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
