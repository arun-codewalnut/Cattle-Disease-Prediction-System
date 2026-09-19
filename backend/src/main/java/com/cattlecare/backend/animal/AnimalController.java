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

    @PostMapping("/api/animals")
    public ResponseEntity<AnimalResponse> create(@Valid @RequestBody CreateAnimalRequest request) {
        Animal animal = animalService.create(request.tagNumber(), request.farmId(), request.species());
        return ResponseEntity.status(HttpStatus.CREATED).body(AnimalResponse.from(animal));
    }
}
