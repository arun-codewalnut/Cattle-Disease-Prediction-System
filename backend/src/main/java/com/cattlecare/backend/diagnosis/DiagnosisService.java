package com.cattlecare.backend.diagnosis;

import java.io.IOException;
import java.util.Base64;
import java.util.Map;
import java.util.Set;

import org.slf4j.MDC;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import com.cattlecare.backend.cattle.Cattle;
import com.cattlecare.backend.cattle.CattleService;
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
    private static final Set<String> ALLOWED_IMAGE_TYPES = Set.of("image/jpeg", "image/png");
    private static final long MAX_IMAGE_SIZE_BYTES = 5L * 1024 * 1024;

    private final CattleService cattleService;
    private final MlServiceClient mlServiceClient;
    private final DiagnosisCaseRepository diagnosisCaseRepository;

    public DiagnosisService(
            CattleService cattleService,
            MlServiceClient mlServiceClient,
            DiagnosisCaseRepository diagnosisCaseRepository) {
        this.cattleService = cattleService;
        this.mlServiceClient = mlServiceClient;
        this.diagnosisCaseRepository = diagnosisCaseRepository;
    }

    public DiagnosisCaseResponse submitSymptoms(Long cattleId, Map<String, Object> symptoms) {
        Cattle cattle = cattleService.getOrThrow(cattleId);

        // If this throws (unreachable / error response), nothing gets persisted below —
        // we don't record a case that never actually got a diagnosis.
        DiagnosisResult result = mlServiceClient.diagnose(symptoms, null);

        String correlationId = MDC.get(CorrelationIdFilter.MDC_KEY);
        DiagnosisCase entity = new DiagnosisCase(
                cattle.getId(),
                correlationId,
                symptoms,
                result.diagnosis(),
                result.confidence(),
                result.recommendedAction());
        diagnosisCaseRepository.save(entity);

        return DiagnosisCaseResponse.from(entity, result.explanation());
    }

    public DiagnosisCaseResponse submitImage(Long cattleId, MultipartFile image) {
        validateImage(image);
        Cattle cattle = cattleService.getOrThrow(cattleId);

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
                cattle.getId(),
                correlationId,
                Map.of(),
                result.diagnosis(),
                result.confidence(),
                result.recommendedAction());
        diagnosisCaseRepository.save(entity);

        return DiagnosisCaseResponse.from(entity, result.explanation());
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
