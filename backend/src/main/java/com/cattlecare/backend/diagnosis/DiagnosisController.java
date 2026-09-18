package com.cattlecare.backend.diagnosis;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.cattlecare.backend.diagnosis.dto.DiagnosisCaseResponse;
import com.cattlecare.backend.diagnosis.dto.SubmitSymptomsRequest;
import jakarta.validation.Valid;

@RestController
public class DiagnosisController {

    private final DiagnosisService diagnosisService;

    public DiagnosisController(DiagnosisService diagnosisService) {
        this.diagnosisService = diagnosisService;
    }

    @PostMapping("/api/animals/{animalId}/diagnoses")
    public ResponseEntity<DiagnosisCaseResponse> submitSymptoms(
            @PathVariable Long animalId, @Valid @RequestBody SubmitSymptomsRequest request) {
        DiagnosisCaseResponse response = diagnosisService.submitSymptoms(animalId, request.symptoms());
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    // M8 phase 1 (docs/specs/M8-image-diagnosis-phase1.md) — image-based diagnosis, backed
    // by a placeholder classifier in ml-service, not a trained model yet.
    @PostMapping(value = "/api/animals/{animalId}/diagnoses/image", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<DiagnosisCaseResponse> submitImage(
            @PathVariable Long animalId, @RequestParam("image") MultipartFile image) {
        DiagnosisCaseResponse response = diagnosisService.submitImage(animalId, image);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
