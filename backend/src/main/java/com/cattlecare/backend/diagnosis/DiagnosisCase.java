package com.cattlecare.backend.diagnosis;

import java.time.Instant;
import java.util.Map;

import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** Maps to the `diagnosis_case` table — see V1__init.sql and
 * V2__rename_cattle_to_animal.sql. `symptoms` is JSONB, mapped via Hibernate's native JSON
 * support (no extra dependency needed). */
@Entity
@Table(name = "diagnosis_case")
public class DiagnosisCase {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "animal_id", nullable = false)
    private Long animalId;

    @Column(name = "correlation_id", nullable = false)
    private String correlationId;

    @JdbcTypeCode(SqlTypes.JSON)
    @Column(name = "symptoms", nullable = false)
    private Map<String, Object> symptoms;

    @Column(name = "diagnosis")
    private String diagnosis;

    @Column(name = "confidence")
    private Double confidence;

    @Column(name = "recommended_action")
    private String recommendedAction;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    protected DiagnosisCase() {
        // JPA
    }

    public DiagnosisCase(
            Long animalId,
            String correlationId,
            Map<String, Object> symptoms,
            String diagnosis,
            Double confidence,
            String recommendedAction) {
        this.animalId = animalId;
        this.correlationId = correlationId;
        this.symptoms = symptoms;
        this.diagnosis = diagnosis;
        this.confidence = confidence;
        this.recommendedAction = recommendedAction;
    }

    public Long getId() {
        return id;
    }

    public Long getAnimalId() {
        return animalId;
    }

    public String getCorrelationId() {
        return correlationId;
    }

    public Map<String, Object> getSymptoms() {
        return symptoms;
    }

    public String getDiagnosis() {
        return diagnosis;
    }

    public Double getConfidence() {
        return confidence;
    }

    public String getRecommendedAction() {
        return recommendedAction;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}
