-- Baseline schema. Add new versioned migrations as V2__..., V3__..., never edit this file
-- once it has run against any database.

CREATE TABLE cattle (
    id BIGSERIAL PRIMARY KEY,
    tag_number VARCHAR(64) NOT NULL UNIQUE,
    farm_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE diagnosis_case (
    id BIGSERIAL PRIMARY KEY,
    cattle_id BIGINT NOT NULL REFERENCES cattle(id),
    correlation_id VARCHAR(64) NOT NULL,
    symptoms JSONB NOT NULL,
    diagnosis VARCHAR(255),
    confidence DOUBLE PRECISION,
    recommended_action VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_diagnosis_case_cattle_id ON diagnosis_case(cattle_id);
CREATE INDEX idx_diagnosis_case_correlation_id ON diagnosis_case(correlation_id);
