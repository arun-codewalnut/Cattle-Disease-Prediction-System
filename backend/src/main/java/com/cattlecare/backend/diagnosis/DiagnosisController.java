package com.cattlecare.backend.diagnosis;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.cattlecare.backend.diagnosis.dto.DiagnosisCaseResponse;
import com.cattlecare.backend.diagnosis.dto.SubmitSymptomsRequest;
import jakarta.validation.Valid;

@RestController
public class DiagnosisController {

    private final DiagnosisService diagnosisService;

    public DiagnosisController(DiagnosisService diagnosisService) {
        this.diagnosisService = diagnosisService;
    }

    @PostMapping("/api/cattle/{cattleId}/diagnoses")
    public ResponseEntity<DiagnosisCaseResponse> submitSymptoms(
            @PathVariable Long cattleId, @Valid @RequestBody SubmitSymptomsRequest request) {
        DiagnosisCaseResponse response = diagnosisService.submitSymptoms(cattleId, request.symptoms());
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
