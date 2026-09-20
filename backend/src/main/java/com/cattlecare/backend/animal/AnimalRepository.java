package com.cattlecare.backend.animal;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface AnimalRepository extends JpaRepository<Animal, Long> {

    Optional<Animal> findByTagNumber(String tagNumber);
}
