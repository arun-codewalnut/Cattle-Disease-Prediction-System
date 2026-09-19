package com.cattlecare.backend.diagnosis;

import java.io.IOException;
import java.util.Base64;
import java.util.Map;
import java.util.Set;

import org.slf4j.MDC;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import com.cattlecare.backend.animal.Animal;
import com.cattlecare.backend.animal.AnimalService;
import com.cattlecare.backend.client.DiagnosisResult;
import com.cattlecare.backend.client.MlServiceClient;
import com.cattlecare.backend.config.ApiException;
import com.cattlecare.backend.config.CorrelationIdFilter;
import com.cattlecare.backend.diagnosis.dto.DiagnosisCaseResponse;

@Service
public class DiagnosisService {

    // M8 phase 1 (docs/specs/M8-image-diagnosis-phase1.md): images are never persisted to
    // disk, only validated, base64-encoded, and forwarded to ml-service for one placeholder
    // prediction — see that spec for why.
    //
    // M11 (docs/specs/M11-buffalo-disease-detection.md): animal.getSpecies() is deliberately
    // NOT forwarded to ml-service here — no buffalo-specific model exists yet, so every
    // species is diagnosed with the same cattle-trained model. The frontend discloses this;
    // don't silently imply species-aware diagnosis by threading the field through before a
    // real model exists to justify it.
    private static final Set<String> ALLOWED_IMAGE_TYPES = Set.of("image/jpeg", "image/png");
    private static final long MAX_IMAGE_SIZE_BYTES = 5L * 1024 * 1024;

    private final AnimalService animalService;
    private final MlServiceClient mlServiceClient;
    private final DiagnosisCaseRepository diagnosisCaseRepository;

    public DiagnosisService(
            AnimalService animalService,
            MlServiceClient mlServiceClient,
            DiagnosisCaseRepository diagnosisCaseRepository) {
        this.animalService = animalService;
        this.mlServiceClient = mlServiceClient;
        this.diagnosisCaseRepository = diagnosisCaseRepository;
    }

    public DiagnosisCaseResponse submitSymptoms(Long animalId, Map<String, Object> symptoms) {
        Animal animal = animalService.getOrThrow(animalId);

        // If this throws (unreachable / error response), nothing gets persisted below —
        // we don't record a case that never actually got a diagnosis.
        DiagnosisResult result = mlServiceClient.diagnose(symptoms, null);

        String correlationId = MDC.get(CorrelationIdFilter.MDC_KEY);
        DiagnosisCase entity = new DiagnosisCase(
                animal.getId(),
                correlationId,
                symptoms,
                result.diagnosis(),
                result.confidence(),
                result.recommendedAction());
        diagnosisCaseRepository.save(entity);

        return DiagnosisCaseResponse.from(entity, result.explanation(), result.precautions(), result.nextSteps());
    }

    public DiagnosisCaseResponse submitImage(Long animalId, MultipartFile image) {
        validateImage(image);
        Animal animal = animalService.getOrThrow(animalId);

        String imageBase64;
        try {
            imageBase64 = Base64.getEncoder().encodeToString(image.getBytes());
        } catch (IOException ex) {
            throw new ApiException(
                    "IMAGE_READ_FAILED", "Could not read the uploaded image.", HttpStatus.BAD_REQUEST);
        }

        // No symptoms for an image-based diagnosis — an empty map, not null, so the
        // ml-service request/DB column contracts (both require a non-null object) hold.
        DiagnosisResult result = mlServiceClient.diagnose(Map.of(), null, imageBase64);

        String correlationId = MDC.get(CorrelationIdFilter.MDC_KEY);
        DiagnosisCase entity = new DiagnosisCase(
                animal.getId(),
                correlationId,
                Map.of(),
                result.diagnosis(),
                result.confidence(),
                result.recommendedAction());
        diagnosisCaseRepository.save(entity);

        return DiagnosisCaseResponse.from(entity, result.explanation(), result.precautions(), result.nextSteps());
    }

    private void validateImage(MultipartFile image) {
        if (image == null || image.isEmpty()) {
            throw new ApiException("IMAGE_REQUIRED", "An image file is required.", HttpStatus.BAD_REQUEST);
        }
        if (!ALLOWED_IMAGE_TYPES.contains(image.getContentType())) {
            throw new ApiException(
                    "UNSUPPORTED_IMAGE_TYPE",
                    "Unsupported image type '" + image.getContentType() + "' — only JPEG and PNG are accepted.",
                    HttpStatus.BAD_REQUEST);
        }
        if (image.getSize() > MAX_IMAGE_SIZE_BYTES) {
            throw new ApiException(
                    "IMAGE_TOO_LARGE", "Image exceeds the 5MB size limit.", HttpStatus.BAD_REQUEST);
        }
    }
}
