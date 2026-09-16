package com.cattlecare.backend.cattle;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** Maps to the `cattle` table — see V1__init.sql. */
@Entity
@Table(name = "cattle")
public class Cattle {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "tag_number", nullable = false, unique = true)
    private String tagNumber;

    @Column(name = "farm_id", nullable = false)
    private Long farmId;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    protected Cattle() {
        // JPA
    }

    public Cattle(String tagNumber, Long farmId) {
        this.tagNumber = tagNumber;
        this.farmId = farmId;
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

    public Instant getCreatedAt() {
        return createdAt;
    }
}
