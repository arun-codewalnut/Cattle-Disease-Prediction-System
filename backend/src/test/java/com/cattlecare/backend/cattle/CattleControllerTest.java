package com.cattlecare.backend.cattle;

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

/** Covers GlobalExceptionHandler's MethodArgumentNotValidException mapping — a blank
 * tagNumber previously leaked Spring's raw validation exception (class names, error codes
 * and all) straight to the frontend as the error "message" instead of a clean, structured
 * ApiError. See docs/DECISIONS.md. */
@WebMvcTest(controllers = CattleController.class)
@Import(GlobalExceptionHandler.class)
class CattleControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private CattleService cattleService;

    @Test
    void blankTagNumber_returnsStructuredValidationError_notARawExceptionDump() throws Exception {
        mockMvc.perform(post("/api/cattle")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"tagNumber\": \"\", \"farmId\": 42}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.code", is("VALIDATION_FAILED")))
                .andExpect(jsonPath("$.details.tagNumber").exists());
    }
}
