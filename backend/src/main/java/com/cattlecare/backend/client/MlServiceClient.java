package com.cattlecare.backend.client;

import org.slf4j.MDC;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientResponseException;

import com.cattlecare.backend.config.ApiException;
import com.cattlecare.backend.config.CorrelationIdFilter;

import java.util.Map;

@Component
public class MlServiceClient {

    private final RestClient restClient;

    // RestClient.builder() is a plain static factory — no Spring bean needed, so this
    // doesn't depend on RestClient auto-configuration being present.
    public MlServiceClient(@Value("${ml-service.base-url}") String baseUrl) {
        this.restClient = RestClient.builder().baseUrl(baseUrl).build();
    }

    public DiagnosisResult diagnose(Map<String, Object> symptoms, String imageUrl) {
        String correlationId = MDC.get(CorrelationIdFilter.MDC_KEY);

        try {
            return restClient.post()
                    .uri("/agent/diagnose")
                    .header(CorrelationIdFilter.HEADER, correlationId)
                    .body(new DiagnoseRequestBody(symptoms, imageUrl))
                    .retrieve()
                    .body(DiagnosisResult.class);
        } catch (ResourceAccessException ex) {
            throw new ApiException(
                    "ML_SERVICE_UNAVAILABLE",
                    "ml-service is unreachable: " + ex.getMessage(),
                    HttpStatus.SERVICE_UNAVAILABLE);
        } catch (RestClientResponseException ex) {
            throw new ApiException(
                    "ML_SERVICE_ERROR",
                    "ml-service returned an error: " + ex.getMessage(),
                    HttpStatus.BAD_GATEWAY);
        }
    }
}
