package com.cattlecare.backend.diagnosis;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.slf4j.MDC;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import com.cattlecare.backend.animal.Animal;
import com.cattlecare.backend.animal.AnimalService;
import com.cattlecare.backend.animal.Species;
import com.cattlecare.backend.client.DiagnosisResult;
import com.cattlecare.backend.client.MlServiceClient;
import com.cattlecare.backend.config.ApiException;
import com.cattlecare.backend.config.CorrelationIdFilter;
import com.cattlecare.backend.diagnosis.dto.DiagnosisCaseResponse;
import com.cattlecare.backend.diagnosis.dto.ImageDiagnosisBatchResponse;

@Service
public class DiagnosisService {

    // M8 phase 1 (docs/specs/M8-image-diagnosis-phase1.md): images are never persisted to
    // disk, only validated, base64-encoded, and forwarded to ml-service for one placeholder
    // prediction — see that spec for why.
    //
    // M12 follow-up (docs/specs/M12-sheep-disease-detection.md): animal.getSpecies() IS now
    // forwarded to ml-service for the symptom path too (it wasn't originally — Buffalo/Sheep
    // both used to silently share the cattle-trained model with no species-aware routing at
    // all). Sheep now routes to its own real, PPR-trained symptom model; every other
    // symptom-diagnosable species still falls back to the cattle model, same as before.
    private static final Set<String> ALLOWED_IMAGE_TYPES = Set.of("image/jpeg", "image/png");
    private static final long MAX_IMAGE_SIZE_BYTES = 5L * 1024 * 1024;

    // Multi-photo follow-up: up to 5 photos per diagnosis attempt, each diagnosed
    // independently against the same trained model (no new ml-service call shape — this is
    // just the existing single-image call, looped) — see ImageDiagnosisBatchResponse for how
    // the 5 results get reconciled into one thing the frontend renders.
    private static final int MAX_IMAGES = 5;

    // M13/M14 (docs/specs/M13-cat-disease-detection.md,
    // docs/specs/M14-dog-disease-detection.md): SYMPTOM diagnosis stays blocked for Cat/Dog —
    // reusing the cattle model's disease list/symptom vocabulary for a companion animal would
    // be an actively wrong result, not a disclosed approximation like Sheep gets.
    static final Set<Species> DIAGNOSIS_SUPPORTED_SPECIES = Set.of(Species.COW, Species.SHEEP);

    // M13/M14 follow-up: Cat and Dog now have their own real, trained IMAGE models (not
    // symptom models) — see ml-service/app/models/cat_image_model.py and dog_image_model.py.
    // Image diagnosis is supported for these in addition to DIAGNOSIS_SUPPORTED_SPECIES;
    // symptom diagnosis stays rejected for them (no symptom model exists for either).
    static final Set<Species> IMAGE_ONLY_SUPPORTED_SPECIES = Set.of(Species.CAT, Species.DOG);

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
        requireSymptomDiagnosisSupported(animal);

        // If this throws (unreachable / error response), nothing gets persisted below —
        // we don't record a case that never actually got a diagnosis. species is forwarded
        // so Sheep routes to its own trained symptom model in ml-service — see this class's
        // header comment.
        DiagnosisResult result = mlServiceClient.diagnose(symptoms, null, null, animal.getSpecies().name());

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

    public ImageDiagnosisBatchResponse submitImage(Long animalId, List<MultipartFile> images) {
        if (images == null || images.isEmpty()) {
            throw new ApiException("IMAGE_REQUIRED", "At least one image file is required.", HttpStatus.BAD_REQUEST);
        }
        if (images.size() > MAX_IMAGES) {
            throw new ApiException(
                    "TOO_MANY_IMAGES",
                    "At most " + MAX_IMAGES + " images are accepted per submission, got " + images.size() + ".",
                    HttpStatus.BAD_REQUEST);
        }
        images.forEach(this::validateImage);

        Animal animal = animalService.getOrThrow(animalId);
        requireImageDiagnosisSupported(animal);
        String correlationId = MDC.get(CorrelationIdFilter.MDC_KEY);

        // Nothing gets persisted if any photo fails partway through — same "no partial case"
        // principle as the rest of this class, just applied to a batch instead of one call.
        List<DiagnosisCaseResponse> results = new ArrayList<>();
        for (MultipartFile image : images) {
            String imageBase64;
            try {
                imageBase64 = Base64.getEncoder().encodeToString(image.getBytes());
            } catch (IOException ex) {
                throw new ApiException(
                        "IMAGE_READ_FAILED", "Could not read the uploaded image.", HttpStatus.BAD_REQUEST);
            }

            // No symptoms for an image-based diagnosis — an empty map, not null, so the
            // ml-service request/DB column contracts (both require a non-null object) hold.
            // species is forwarded so Cat/Dog route to their own trained image models in
            // ml-service — see DiagnosisService's class comment.
            DiagnosisResult result =
                    mlServiceClient.diagnose(Map.of(), null, imageBase64, animal.getSpecies().name());

            DiagnosisCase entity = new DiagnosisCase(
                    animal.getId(),
                    correlationId,
                    Map.of(),
                    result.diagnosis(),
                    result.confidence(),
                    result.recommendedAction());
            diagnosisCaseRepository.save(entity);

            results.add(DiagnosisCaseResponse.from(
                    entity, result.explanation(), result.precautions(), result.nextSteps()));
        }

        return ImageDiagnosisBatchResponse.from(results);
    }

    private void requireSymptomDiagnosisSupported(Animal animal) {
        if (!DIAGNOSIS_SUPPORTED_SPECIES.contains(animal.getSpecies())) {
            throw new ApiException(
                    "DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES",
                    "Symptom-based diagnosis isn't available for species " + animal.getSpecies() + ".",
                    HttpStatus.BAD_REQUEST);
        }
    }

    private void requireImageDiagnosisSupported(Animal animal) {
        Species species = animal.getSpecies();
        if (!DIAGNOSIS_SUPPORTED_SPECIES.contains(species) && !IMAGE_ONLY_SUPPORTED_SPECIES.contains(species)) {
            throw new ApiException(
                    "DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES",
                    "Image-based diagnosis isn't available for species " + species + ".",
                    HttpStatus.BAD_REQUEST);
        }
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
