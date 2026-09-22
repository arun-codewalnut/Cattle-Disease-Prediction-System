package com.cattlecare.backend.diagnosis;

import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.cattlecare.backend.diagnosis.dto.DiagnosisCaseResponse;
import com.cattlecare.backend.diagnosis.dto.ImageDiagnosisBatchResponse;
import com.cattlecare.backend.diagnosis.dto.SubmitSymptomsRequest;
import jakarta.validation.Valid;

/** Diagnosis is a single call now. It used to require registering an animal first
 * (POST /api/animals) and then posting to /api/animals/{animalId}/diagnoses — animal
 * identity (tag number, farm ID, the record itself) was removed because none of it reached
 * the model. See docs/specs/remove-animal-identity.md. */
@RestController
public class DiagnosisController {

    private final DiagnosisService diagnosisService;

    public DiagnosisController(DiagnosisService diagnosisService) {
        this.diagnosisService = diagnosisService;
    }

    @PostMapping("/api/diagnoses")
    public ResponseEntity<DiagnosisCaseResponse> submitSymptoms(@Valid @RequestBody SubmitSymptomsRequest request) {
        DiagnosisCaseResponse response = diagnosisService.submitSymptoms(request.species(), request.symptoms());
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    // M8 phase 1 (docs/specs/M8-image-diagnosis-phase1.md) — image-based diagnosis. Accepts
    // 1-5 photos (multi-photo follow-up); each is diagnosed independently and the response
    // says whether they all agreed — see ImageDiagnosisBatchResponse.
    //
    // species travels as a form field here rather than a JSON body, since this endpoint is
    // multipart — a missing or unparseable value is handled in GlobalExceptionHandler so it
    // returns the same {code, message, details} shape as the JSON path.
    @PostMapping(value = "/api/diagnoses/image", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ResponseEntity<ImageDiagnosisBatchResponse> submitImage(
            @RequestParam("species") Species species, @RequestParam("images") List<MultipartFile> images) {
        ImageDiagnosisBatchResponse response = diagnosisService.submitImage(species, images);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }
}
