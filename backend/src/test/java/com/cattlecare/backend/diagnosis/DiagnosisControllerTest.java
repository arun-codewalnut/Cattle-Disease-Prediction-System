package com.cattlecare.backend.diagnosis;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.cattlecare.backend.client.DiagnosisResult;
import com.cattlecare.backend.diagnosis.dto.DiagnosisCaseResponse;
import com.cattlecare.backend.diagnosis.dto.ImageDiagnosisBatchResponse;

/** First real HTTP-layer test for this controller — everything else exercises
 * {@link DiagnosisService} directly with a mocked {@code MlServiceClient}, which never
 * touches {@link com.cattlecare.backend.config.GlobalExceptionHandler} at all. Added after
 * full-scenario testing found a real gap there: calling {@code POST /api/diagnoses/image}
 * with a non-multipart content type (some HTTP clients send this when there's nothing to
 * attach) fell through to the generic exception handler as a raw {@code 500} leaking
 * {@code HttpMediaTypeNotSupportedException}'s message — the same class of bug this file's
 * handler already fixed twice for other exception types. */
@WebMvcTest(DiagnosisController.class)
class DiagnosisControllerTest {

    @Autowired
    private MockMvc mvc;

    @MockitoBean
    private DiagnosisService diagnosisService;

    @Test
    void submitImage_wrongContentType_returnsCleanImageRequiredNotA500() throws Exception {
        // No multipart part at all — Spring rejects the content type itself, before
        // @RequestParam binding runs, a different failure mode than
        // MissingServletRequestPartException (a genuinely empty multipart request).
        mvc.perform(post("/api/diagnoses/image")
                        .contentType(MediaType.APPLICATION_FORM_URLENCODED)
                        .content("species=COW"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("IMAGE_REQUIRED"));
    }

    @Test
    void submitImage_missingSpeciesFormField_returnsValidationFailed() throws Exception {
        MockMultipartFile image = new MockMultipartFile("images", "cow.jpg", "image/jpeg", new byte[] {1});

        mvc.perform(multipart("/api/diagnoses/image").file(image))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("VALIDATION_FAILED"));
    }

    @Test
    void submitImage_invalidSpeciesValue_returnsInvalidRequestBody() throws Exception {
        MockMultipartFile image = new MockMultipartFile("images", "cow.jpg", "image/jpeg", new byte[] {1});

        mvc.perform(multipart("/api/diagnoses/image").file(image).param("species", "LLAMA"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("INVALID_REQUEST_BODY"));
    }

    @Test
    void submitImage_validRequest_returns201WithServiceResult() throws Exception {
        DiagnosisResult mlResult = new DiagnosisResult(
                "Healthy", 0.9, "x", "monitor", List.of(), List.of(), List.of());
        when(diagnosisService.submitImage(any(), any()))
                .thenReturn(ImageDiagnosisBatchResponse.from(List.of(DiagnosisCaseResponse.from(Species.COW, mlResult))));

        MockMultipartFile image = new MockMultipartFile("images", "cow.jpg", "image/jpeg", new byte[] {1});

        mvc.perform(multipart("/api/diagnoses/image").file(image).param("species", "COW"))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.results[0].diagnosis").value("Healthy"));
    }

    @Test
    void submitSymptoms_missingSpecies_returnsValidationFailed() throws Exception {
        mvc.perform(post("/api/diagnoses")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"symptoms\": {}}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code").value("VALIDATION_FAILED"));
    }
}
