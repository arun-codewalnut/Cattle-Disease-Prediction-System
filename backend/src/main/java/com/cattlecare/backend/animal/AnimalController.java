package com.cattlecare.backend.animal;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.cattlecare.backend.animal.dto.AnimalResponse;
import com.cattlecare.backend.animal.dto.CreateAnimalRequest;
import jakarta.validation.Valid;

@RestController
public class AnimalController {

    private final AnimalService animalService;

    public AnimalController(AnimalService animalService) {
        this.animalService = animalService;
    }

    // find-or-create by tag number (AnimalService.findOrCreate) — always 201 here regardless
    // of whether this call created a new record or reused an existing one, same "don't add
    // ceremony beyond what's needed" precedent the rest of this API already follows.
    @PostMapping("/api/animals")
    public ResponseEntity<AnimalResponse> create(@Valid @RequestBody CreateAnimalRequest request) {
        Animal animal = animalService.findOrCreate(request.tagNumber(), request.farmId(), request.species());
        return ResponseEntity.status(HttpStatus.CREATED).body(AnimalResponse.from(animal));
    }
}
