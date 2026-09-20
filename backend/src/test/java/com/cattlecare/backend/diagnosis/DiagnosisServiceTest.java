package com.cattlecare.backend.diagnosis;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.multipart.MultipartFile;

import com.cattlecare.backend.animal.Animal;
import com.cattlecare.backend.animal.AnimalService;
import com.cattlecare.backend.animal.Species;
import com.cattlecare.backend.client.DiagnosisResult;
import com.cattlecare.backend.client.MlServiceClient;
import com.cattlecare.backend.config.ApiException;
import com.cattlecare.backend.diagnosis.dto.DiagnosisCaseResponse;

class DiagnosisServiceTest {

    private final AnimalService animalService = mock(AnimalService.class);
    private final MlServiceClient mlServiceClient = mock(MlServiceClient.class);
    private final DiagnosisCaseRepository diagnosisCaseRepository = mock(DiagnosisCaseRepository.class);
    private final DiagnosisService diagnosisService =
            new DiagnosisService(animalService, mlServiceClient, diagnosisCaseRepository);

    @Test
    void submitSymptoms_success_persistsAndReturnsDiagnosis() {
        Animal animal = new Animal("COW-001", 42L, Species.COW);
        when(animalService.getOrThrow(1L)).thenReturn(animal);

        DiagnosisResult mlResult = new DiagnosisResult(
                "Foot and Mouth Disease", 0.81, "Predicted FMD...", "escalate_to_vet", List.of(),
                List.of("Isolate the animal."), List.of("Contact your vet immediately."));
        when(mlServiceClient.diagnose(anyMap(), any())).thenReturn(mlResult);

        Map<String, Object> symptoms = Map.of("fever", true);
        DiagnosisCaseResponse response = diagnosisService.submitSymptoms(1L, symptoms);

        assertEquals("Foot and Mouth Disease", response.diagnosis());
        assertEquals(0.81, response.confidence());
        assertEquals("escalate_to_vet", response.recommendedAction());
        assertEquals(List.of("Isolate the animal."), response.precautions());
        assertEquals(List.of("Contact your vet immediately."), response.nextSteps());
        verify(diagnosisCaseRepository).save(any(DiagnosisCase.class));
    }

    @Test
    void submitSymptoms_animalNotFound_neverCallsMlService() {
        when(animalService.getOrThrow(999L))
                .thenThrow(new ApiException("ANIMAL_NOT_FOUND", "not found", HttpStatus.NOT_FOUND));

        assertThrows(ApiException.class, () -> diagnosisService.submitSymptoms(999L, Map.of()));

        verify(mlServiceClient, never()).diagnose(anyMap(), any());
        verify(diagnosisCaseRepository, never()).save(any());
    }

    @Test
    void submitSymptoms_mlServiceUnavailable_doesNotPersistACase() {
        Animal animal = new Animal("COW-001", 42L, Species.COW);
        when(animalService.getOrThrow(1L)).thenReturn(animal);
        when(mlServiceClient.diagnose(anyMap(), any()))
                .thenThrow(new ApiException("ML_SERVICE_UNAVAILABLE", "unreachable", HttpStatus.SERVICE_UNAVAILABLE));

        ApiException ex = assertThrows(ApiException.class, () -> diagnosisService.submitSymptoms(1L, Map.of()));

        assertEquals("ML_SERVICE_UNAVAILABLE", ex.getCode());
        verify(diagnosisCaseRepository, never()).save(any());
    }

    @Test
    void submitSymptoms_mlServiceErrorResponse_doesNotPersistACase() {
        Animal animal = new Animal("COW-001", 42L, Species.COW);
        when(animalService.getOrThrow(1L)).thenReturn(animal);
        when(mlServiceClient.diagnose(anyMap(), any()))
                .thenThrow(new ApiException("ML_SERVICE_ERROR", "bad response", HttpStatus.BAD_GATEWAY));

        ApiException ex = assertThrows(ApiException.class, () -> diagnosisService.submitSymptoms(1L, Map.of()));

        assertEquals("ML_SERVICE_ERROR", ex.getCode());
        verify(diagnosisCaseRepository, never()).save(any());
    }

    @Test
    void submitImage_success_encodesAsBase64AndPersistsWithEmptySymptoms() {
        Animal animal = new Animal("COW-001", 42L, Species.COW);
        when(animalService.getOrThrow(1L)).thenReturn(animal);

        DiagnosisResult mlResult = new DiagnosisResult(
                "Lumpy Skin Disease", 0.5, "This is a placeholder image-based prediction...",
                "escalate_to_vet", List.of(), List.of(), List.of());
        when(mlServiceClient.diagnose(eq(Map.of()), isNull(), anyString())).thenReturn(mlResult);

        MultipartFile image = new MockMultipartFile("image", "cow.jpg", "image/jpeg", new byte[] {1, 2, 3});
        DiagnosisCaseResponse response = diagnosisService.submitImage(1L, image);

        assertEquals("Lumpy Skin Disease", response.diagnosis());
        assertEquals("escalate_to_vet", response.recommendedAction());
        verify(mlServiceClient).diagnose(eq(Map.of()), isNull(), eq("AQID")); // base64("\x01\x02\x03")
        verify(diagnosisCaseRepository).save(any(DiagnosisCase.class));
    }

    @Test
    void submitImage_unsupportedType_rejectedBeforeAnimalLookupOrMlServiceCall() {
        MultipartFile image = new MockMultipartFile("image", "cow.gif", "image/gif", new byte[] {1});

        ApiException ex = assertThrows(ApiException.class, () -> diagnosisService.submitImage(1L, image));

        assertEquals("UNSUPPORTED_IMAGE_TYPE", ex.getCode());
        verify(animalService, never()).getOrThrow(any());
        verify(mlServiceClient, never()).diagnose(anyMap(), any(), any());
    }

    @Test
    void submitImage_tooLarge_rejectedBeforeAnimalLookupOrMlServiceCall() {
        byte[] oversized = new byte[6 * 1024 * 1024];
        MultipartFile image = new MockMultipartFile("image", "cow.jpg", "image/jpeg", oversized);

        ApiException ex = assertThrows(ApiException.class, () -> diagnosisService.submitImage(1L, image));

        assertEquals("IMAGE_TOO_LARGE", ex.getCode());
        verify(animalService, never()).getOrThrow(any());
        verify(mlServiceClient, never()).diagnose(anyMap(), any(), any());
    }

    @Test
    void submitImage_missingFile_rejected() {
        MultipartFile empty = new MockMultipartFile("image", "empty.jpg", "image/jpeg", new byte[0]);

        ApiException ex = assertThrows(ApiException.class, () -> diagnosisService.submitImage(1L, empty));

        assertEquals("IMAGE_REQUIRED", ex.getCode());
    }

    @Test
    void submitImage_animalNotFound_neverCallsMlService() {
        MultipartFile image = new MockMultipartFile("image", "cow.jpg", "image/jpeg", new byte[] {1});
        when(animalService.getOrThrow(999L))
                .thenThrow(new ApiException("ANIMAL_NOT_FOUND", "not found", HttpStatus.NOT_FOUND));

        assertThrows(ApiException.class, () -> diagnosisService.submitImage(999L, image));

        verify(mlServiceClient, never()).diagnose(anyMap(), any(), any());
        verify(diagnosisCaseRepository, never()).save(any());
    }

    // M13/M14 (docs/specs/M13-cat-disease-detection.md,
    // docs/specs/M14-dog-disease-detection.md): the cattle model's disease list and symptom
    // vocabulary don't apply to a cat or dog at all, unlike Buffalo/Sheep - diagnosis must be
    // rejected outright, not silently run through the cattle model.

    @Test
    void submitSymptoms_catSpecies_rejectedBeforeMlServiceCall() {
        Animal cat = new Animal("CAT-001", 5L, Species.CAT);
        when(animalService.getOrThrow(1L)).thenReturn(cat);

        ApiException ex = assertThrows(ApiException.class, () -> diagnosisService.submitSymptoms(1L, Map.of()));

        assertEquals("DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES", ex.getCode());
        verify(mlServiceClient, never()).diagnose(anyMap(), any());
        verify(diagnosisCaseRepository, never()).save(any());
    }

    @Test
    void submitImage_catSpecies_rejectedBeforeMlServiceCall() {
        Animal cat = new Animal("CAT-001", 5L, Species.CAT);
        when(animalService.getOrThrow(1L)).thenReturn(cat);
        MultipartFile image = new MockMultipartFile("image", "cat.jpg", "image/jpeg", new byte[] {1});

        ApiException ex = assertThrows(ApiException.class, () -> diagnosisService.submitImage(1L, image));

        assertEquals("DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES", ex.getCode());
        verify(mlServiceClient, never()).diagnose(anyMap(), any(), any());
        verify(diagnosisCaseRepository, never()).save(any());
    }

    @Test
    void submitSymptoms_dogSpecies_rejectedBeforeMlServiceCall() {
        Animal dog = new Animal("DOG-001", 5L, Species.DOG);
        when(animalService.getOrThrow(1L)).thenReturn(dog);

        ApiException ex = assertThrows(ApiException.class, () -> diagnosisService.submitSymptoms(1L, Map.of()));

        assertEquals("DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES", ex.getCode());
        verify(mlServiceClient, never()).diagnose(anyMap(), any());
        verify(diagnosisCaseRepository, never()).save(any());
    }

    @Test
    void submitImage_dogSpecies_rejectedBeforeMlServiceCall() {
        Animal dog = new Animal("DOG-001", 5L, Species.DOG);
        when(animalService.getOrThrow(1L)).thenReturn(dog);
        MultipartFile image = new MockMultipartFile("image", "dog.jpg", "image/jpeg", new byte[] {1});

        ApiException ex = assertThrows(ApiException.class, () -> diagnosisService.submitImage(1L, image));

        assertEquals("DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES", ex.getCode());
        verify(mlServiceClient, never()).diagnose(anyMap(), any(), any());
        verify(diagnosisCaseRepository, never()).save(any());
    }
}
