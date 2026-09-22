package com.cattlecare.backend.diagnosis;

import java.time.Instant;
import java.util.Map;

import org.hibernate.annotations.JdbcTypeCode;
import org.hibernate.type.SqlTypes;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/** Maps to the `diagnosis_case` table — see V1__init.sql through
 * V4__remove_animal_identity.sql. `symptoms` is JSONB, mapped via Hibernate's native JSON
 * support (no extra dependency needed).
 *
 * <p>`species` used to live on the animal this case pointed at. Animal identity (tag number,
 * farm ID, and the record itself) was removed — see docs/specs/remove-animal-identity.md —
 * so the case carries its own species now. It's the one piece of that record worth keeping:
 * it selects which trained model ran, so a stored case is only interpretable alongside it. */
@Entity
@Table(name = "diagnosis_case")
public class DiagnosisCase {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Enumerated(EnumType.STRING)
    @Column(name = "species", nullable = false)
    private Species species;

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
            Species species,
            String correlationId,
            Map<String, Object> symptoms,
            String diagnosis,
            Double confidence,
            String recommendedAction) {
        this.species = species;
        this.correlationId = correlationId;
        this.symptoms = symptoms;
        this.diagnosis = diagnosis;
        this.confidence = confidence;
        this.recommendedAction = recommendedAction;
    }

    public Long getId() {
        return id;
    }

    public Species getSpecies() {
        return species;
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
