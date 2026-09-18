package com.cattlecare.backend.animal;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** Maps to the `animal` table — see V2__rename_cattle_to_animal.sql. Renamed from `Cattle`
 * in M11 (docs/specs/M11-buffalo-disease-detection.md) when the domain generalized beyond
 * cattle-only. */
@Entity
@Table(name = "animal")
public class Animal {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "tag_number", nullable = false, unique = true)
    private String tagNumber;

    @Column(name = "farm_id", nullable = false)
    private Long farmId;

    @Enumerated(EnumType.STRING)
    @Column(name = "species", nullable = false)
    private Species species;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    protected Animal() {
        // JPA
    }

    public Animal(String tagNumber, Long farmId, Species species) {
        this.tagNumber = tagNumber;
        this.farmId = farmId;
        this.species = species;
    }

    public Long getId() {
        return id;
    }

    public String getTagNumber() {
        return tagNumber;
    }

    public Long getFarmId() {
        return farmId;
    }

    public Species getSpecies() {
        return species;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
