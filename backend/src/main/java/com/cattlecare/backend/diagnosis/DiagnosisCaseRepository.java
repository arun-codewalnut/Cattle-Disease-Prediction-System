package com.cattlecare.backend.diagnosis;

import org.springframework.data.jpa.repository.JpaRepository;

public interface DiagnosisCaseRepository extends JpaRepository<DiagnosisCase, Long> {
}
