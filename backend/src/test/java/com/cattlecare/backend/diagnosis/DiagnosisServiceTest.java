package com.cattlecare.backend.diagnosis;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.ArgumentMatchers.isNull;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import java.util.List;
import java.util.Map;

import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.web.multipart.MultipartFile;

import com.cattlecare.backend.client.DiagnosisResult;
import com.cattlecare.backend.client.MlServiceClient;
import com.cattlecare.backend.config.ApiException;
import com.cattlecare.backend.diagnosis.dto.DiagnosisCaseResponse;
import com.cattlecare.backend.diagnosis.dto.ImageDiagnosisBatchResponse;

/** Species arrives directly on the request (docs/specs/remove-animal-identity.md) and
 * nothing is persisted (docs/specs/remove-databases.md), so the service under test is a
 * validating gateway over one ml-service call. */
class DiagnosisServiceTest {

    private final MlServiceClient mlServiceClient = mock(MlServiceClient.class);
    private final DiagnosisService diagnosisService = new DiagnosisService(mlServiceClient);

    @Test
    void submitSymptoms_success_returnsDiagnosis() {
        DiagnosisResult mlResult = new DiagnosisResult(
                "Foot and Mouth Disease", 0.81, "Predicted FMD...", "escalate_to_vet", List.of(),
                List.of("Isolate the animal."), List.of("Contact your vet immediately."));
        when(mlServiceClient.diagnose(anyMap(), isNull(), isNull(), eq("COW"))).thenReturn(mlResult);

        Map<String, Object> symptoms = Map.of("fever", true);
        DiagnosisCaseResponse response = diagnosisService.submitSymptoms(Species.COW, symptoms);

        assertEquals("Foot and Mouth Disease", response.diagnosis());
        assertEquals(0.81, response.confidence());
        assertEquals("escalate_to_vet", response.recommendedAction());
        assertEquals(List.of("Isolate the animal."), response.precautions());
        assertEquals(List.of("Contact your vet immediately."), response.nextSteps());
    }

    // The species the caller asked for must come back on the response, not a default — a
    // result is only interpretable alongside the model that produced it.
    @Test
    void submitSymptoms_returnsTheRequestedSpecies() {
        DiagnosisResult mlResult = new DiagnosisResult(
                "PPR (Peste des Petits Ruminants)", 0.77, "Predicted PPR.", "escalate_to_vet",
                List.of(), List.of(), List.of());
        when(mlServiceClient.diagnose(anyMap(), isNull(), isNull(), eq("SHEEP"))).thenReturn(mlResult);

        DiagnosisCaseResponse response = diagnosisService.submitSymptoms(Species.SHEEP, Map.of("diarrhea", true));

        assertEquals(Species.SHEEP, response.species());
        assertEquals("PPR (Peste des Petits Ruminants)", response.diagnosis());
    }

    @Test
    void submitSymptoms_mlServiceUnavailable_surfacesTheError() {
        when(mlServiceClient.diagnose(anyMap(), isNull(), isNull(), eq("COW")))
                .thenThrow(new ApiException("ML_SERVICE_UNAVAILABLE", "unreachable", HttpStatus.SERVICE_UNAVAILABLE));

        ApiException ex =
                assertThrows(ApiException.class, () -> diagnosisService.submitSymptoms(Species.COW, Map.of()));

        assertEquals("ML_SERVICE_UNAVAILABLE", ex.getCode());
    }

    @Test
    void submitSymptoms_mlServiceErrorResponse_surfacesTheError() {
        when(mlServiceClient.diagnose(anyMap(), isNull(), isNull(), eq("COW")))
                .thenThrow(new ApiException("ML_SERVICE_ERROR", "bad response", HttpStatus.BAD_GATEWAY));

        ApiException ex =
                assertThrows(ApiException.class, () -> diagnosisService.submitSymptoms(Species.COW, Map.of()));

        assertEquals("ML_SERVICE_ERROR", ex.getCode());
    }

    @Test
    void submitImage_success_encodesAsBase64AndSendsEmptySymptoms() {
        DiagnosisResult mlResult = new DiagnosisResult(
                "Lumpy Skin Disease", 0.5, "This is a placeholder image-based prediction...",
                "escalate_to_vet", List.of(), List.of(), List.of());
        when(mlServiceClient.diagnose(eq(Map.of()), isNull(), anyString(), eq("COW"))).thenReturn(mlResult);

        MultipartFile image = new MockMultipartFile("image", "cow.jpg", "image/jpeg", new byte[] {1, 2, 3});
        ImageDiagnosisBatchResponse response = diagnosisService.submitImage(Species.COW, List.of(image));

        assertEquals(1, response.results().size());
        assertEquals("Lumpy Skin Disease", response.results().get(0).diagnosis());
        assertEquals("escalate_to_vet", response.results().get(0).recommendedAction());
        assertTrue(response.diagnosesAgree()); // a single photo always agrees with itself
        verify(mlServiceClient).diagnose(eq(Map.of()), isNull(), eq("AQID"), eq("COW")); // base64("\x01\x02\x03")
    }

    // Multi-photo follow-up: up to 5 photos per submission, each diagnosed independently.

    @Test
    void submitImage_multiplePhotosAllSameDiagnosis_agrees() {
        DiagnosisResult mlResult = new DiagnosisResult(
                "Healthy", 0.9, "Predicted Healthy.", "monitor", List.of(), List.of(), List.of());
        when(mlServiceClient.diagnose(eq(Map.of()), isNull(), anyString(), eq("COW"))).thenReturn(mlResult);

        MultipartFile a = new MockMultipartFile("images", "a.jpg", "image/jpeg", new byte[] {1});
        MultipartFile b = new MockMultipartFile("images", "b.jpg", "image/jpeg", new byte[] {2});
        MultipartFile c = new MockMultipartFile("images", "c.jpg", "image/jpeg", new byte[] {3});

        ImageDiagnosisBatchResponse response = diagnosisService.submitImage(Species.COW, List.of(a, b, c));

        assertEquals(3, response.results().size());
        assertTrue(response.diagnosesAgree());
    }

    @Test
    void submitImage_multiplePhotosDisagreeingDiagnoses_flagsDisagreement() {
        DiagnosisResult ringworm = new DiagnosisResult(
                "Ringworm", 0.9, "Predicted Ringworm.", "consult_vet", List.of(), List.of(), List.of());
        DiagnosisResult scabies = new DiagnosisResult(
                "Scabies", 0.85, "Predicted Scabies.", "consult_vet", List.of(), List.of(), List.of());
        when(mlServiceClient.diagnose(eq(Map.of()), isNull(), eq("AQ=="), eq("CAT"))).thenReturn(ringworm); // "\x01"
        when(mlServiceClient.diagnose(eq(Map.of()), isNull(), eq("Ag=="), eq("CAT"))).thenReturn(ringworm); // "\x02"
        when(mlServiceClient.diagnose(eq(Map.of()), isNull(), eq("Aw=="), eq("CAT"))).thenReturn(scabies); // "\x03"

        MultipartFile a = new MockMultipartFile("images", "a.jpg", "image/jpeg", new byte[] {1});
        MultipartFile b = new MockMultipartFile("images", "b.jpg", "image/jpeg", new byte[] {2});
        MultipartFile c = new MockMultipartFile("images", "c.jpg", "image/jpeg", new byte[] {3});

        ImageDiagnosisBatchResponse response = diagnosisService.submitImage(Species.CAT, List.of(a, b, c));

        assertEquals(3, response.results().size());
        assertFalse(response.diagnosesAgree());
    }

    // M15 (docs/specs/M15-image-diagnosis-quality-gate.md): a photo ml-service's species
    // gate rejects as not-an-animal comes back as diagnosis "invalid_image" — not a real
    // diagnosis to agree or disagree with the others in the batch.
    @Test
    void submitImage_matchingDiagnosesPlusOneInvalidImage_stillAgrees() {
        DiagnosisResult ringworm = new DiagnosisResult(
                "Ringworm", 0.9, "Predicted Ringworm.", "consult_vet", List.of(), List.of(), List.of());
        DiagnosisResult invalidImage = new DiagnosisResult(
                "invalid_image", 0.0, "This doesn't look like a photo of an animal.", "retry_upload",
                List.of(), List.of(), List.of());
        when(mlServiceClient.diagnose(eq(Map.of()), isNull(), eq("AQ=="), eq("CAT"))).thenReturn(ringworm); // "\x01"
        when(mlServiceClient.diagnose(eq(Map.of()), isNull(), eq("Ag=="), eq("CAT"))).thenReturn(ringworm); // "\x02"
        when(mlServiceClient.diagnose(eq(Map.of()), isNull(), eq("Aw=="), eq("CAT"))).thenReturn(invalidImage);

        MultipartFile a = new MockMultipartFile("images", "a.jpg", "image/jpeg", new byte[] {1});
        MultipartFile b = new MockMultipartFile("images", "b.jpg", "image/jpeg", new byte[] {2});
        MultipartFile c = new MockMultipartFile("images", "car.jpg", "image/jpeg", new byte[] {3});

        ImageDiagnosisBatchResponse response = diagnosisService.submitImage(Species.CAT, List.of(a, b, c));

        assertEquals(3, response.results().size());
        assertTrue(response.diagnosesAgree());
        assertEquals("invalid_image", response.results().get(2).diagnosis());
    }

    @Test
    void submitImage_moreThanFivePhotos_rejectedBeforeMlServiceCall() {
        List<MultipartFile> sixImages = java.util.stream.IntStream.range(0, 6)
                .mapToObj(i -> (MultipartFile) new MockMultipartFile(
                        "images", "img" + i + ".jpg", "image/jpeg", new byte[] {(byte) i}))
                .toList();

        ApiException ex =
                assertThrows(ApiException.class, () -> diagnosisService.submitImage(Species.COW, sixImages));

        assertEquals("TOO_MANY_IMAGES", ex.getCode());
        verifyNoInteractions(mlServiceClient);
    }

    @Test
    void submitImage_unsupportedType_rejectedBeforeMlServiceCall() {
        MultipartFile image = new MockMultipartFile("image", "cow.gif", "image/gif", new byte[] {1});

        ApiException ex =
                assertThrows(ApiException.class, () -> diagnosisService.submitImage(Species.COW, List.of(image)));

        assertEquals("UNSUPPORTED_IMAGE_TYPE", ex.getCode());
        verifyNoInteractions(mlServiceClient);
    }

    @Test
    void submitImage_tooLarge_rejectedBeforeMlServiceCall() {
        byte[] oversized = new byte[6 * 1024 * 1024];
        MultipartFile image = new MockMultipartFile("image", "cow.jpg", "image/jpeg", oversized);

        ApiException ex =
                assertThrows(ApiException.class, () -> diagnosisService.submitImage(Species.COW, List.of(image)));

        assertEquals("IMAGE_TOO_LARGE", ex.getCode());
        verifyNoInteractions(mlServiceClient);
    }

    @Test
    void submitImage_missingFile_rejected() {
        ApiException ex =
                assertThrows(ApiException.class, () -> diagnosisService.submitImage(Species.COW, List.of()));

        assertEquals("IMAGE_REQUIRED", ex.getCode());
        verifyNoInteractions(mlServiceClient);
    }

    // M13/M14 (docs/specs/M13-cat-disease-detection.md,
    // docs/specs/M14-dog-disease-detection.md): the cattle model's disease list and symptom
    // vocabulary don't apply to a cat or dog at all, unlike Sheep - SYMPTOM diagnosis
    // must be rejected outright, not silently run through the cattle model.

    @Test
    void submitSymptoms_catSpecies_rejectedBeforeMlServiceCall() {
        ApiException ex =
                assertThrows(ApiException.class, () -> diagnosisService.submitSymptoms(Species.CAT, Map.of()));

        assertEquals("DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES", ex.getCode());
        verifyNoInteractions(mlServiceClient);
    }

    @Test
    void submitSymptoms_dogSpecies_rejectedBeforeMlServiceCall() {
        ApiException ex =
                assertThrows(ApiException.class, () -> diagnosisService.submitSymptoms(Species.DOG, Map.of()));

        assertEquals("DIAGNOSIS_NOT_SUPPORTED_FOR_SPECIES", ex.getCode());
        verifyNoInteractions(mlServiceClient);
    }

    // M13/M14 follow-up: Cat/Dog now have their own real, trained IMAGE models (not symptom
    // models) — image diagnosis succeeds for them and forwards species so ml-service can pick
    // the right model. Symptom diagnosis (above) stays rejected — no symptom model exists.

    @Test
    void submitImage_catSpecies_succeedsAndForwardsSpecies() {
        DiagnosisResult mlResult = new DiagnosisResult(
                "Ringworm", 0.91, "Predicted Ringworm with 91% confidence.", "consult_vet",
                List.of(), List.of(), List.of());
        when(mlServiceClient.diagnose(eq(Map.of()), isNull(), anyString(), eq("CAT"))).thenReturn(mlResult);
        MultipartFile image = new MockMultipartFile("image", "cat.jpg", "image/jpeg", new byte[] {1});

        ImageDiagnosisBatchResponse response = diagnosisService.submitImage(Species.CAT, List.of(image));

        assertEquals("Ringworm", response.results().get(0).diagnosis());
        verify(mlServiceClient).diagnose(eq(Map.of()), isNull(), anyString(), eq("CAT"));
    }

    @Test
    void submitImage_dogSpecies_succeedsAndForwardsSpecies() {
        DiagnosisResult mlResult = new DiagnosisResult(
                "Mange", 0.99, "Predicted Mange with 99% confidence.", "consult_vet",
                List.of(), List.of(), List.of());
        when(mlServiceClient.diagnose(eq(Map.of()), isNull(), anyString(), eq("DOG"))).thenReturn(mlResult);
        MultipartFile image = new MockMultipartFile("image", "dog.jpg", "image/jpeg", new byte[] {1});

        ImageDiagnosisBatchResponse response = diagnosisService.submitImage(Species.DOG, List.of(image));

        assertEquals("Mange", response.results().get(0).diagnosis());
        verify(mlServiceClient).diagnose(eq(Map.of()), isNull(), anyString(), eq("DOG"));
    }
}
