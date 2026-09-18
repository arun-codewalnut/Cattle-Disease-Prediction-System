package com.cattlecare.backend.animal;

import static org.hamcrest.Matchers.is;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.cattlecare.backend.config.GlobalExceptionHandler;

/** Covers GlobalExceptionHandler's MethodArgumentNotValidException and
 * HttpMessageNotReadableException mappings — a blank tagNumber, or an invalid `species`
 * value, previously leaked a raw exception (class names, error codes and all) straight to
 * the frontend as the error "message" instead of a clean, structured ApiError. See
 * docs/DECISIONS.md. */
@WebMvcTest(controllers = AnimalController.class)
@Import(GlobalExceptionHandler.class)
class AnimalControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private AnimalService animalService;

    @Test
    void blankTagNumber_returnsStructuredValidationError_notARawExceptionDump() throws Exception {
        mockMvc.perform(post("/api/animals")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"tagNumber\": \"\", \"farmId\": 42, \"species\": \"COW\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code", is("VALIDATION_FAILED")))
                .andExpect(jsonPath("$.details.tagNumber").exists());
    }

    @Test
    void invalidSpecies_returnsStructuredErrorNotARawJacksonDump() throws Exception {
        mockMvc.perform(post("/api/animals")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"tagNumber\": \"X-1\", \"farmId\": 42, \"species\": \"GOAT\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code", is("INVALID_REQUEST_BODY")));
    }
}
