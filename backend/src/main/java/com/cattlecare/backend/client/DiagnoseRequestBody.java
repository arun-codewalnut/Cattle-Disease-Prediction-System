package com.cattlecare.backend.client;

import java.util.Map;

import com.fasterxml.jackson.annotation.JsonProperty;

/** Request body sent to ml-service's POST /agent/diagnose — see docs/API_CONTRACTS.md.
 * ml-service's schema is snake_case (Pydantic default) — explicit here rather than relying
 * on Jackson's default camelCase, since this is a cross-service contract. */
public record DiagnoseRequestBody(
        Map<String, Object> symptoms,
        @JsonProperty("image_url") String imageUrl,
        @JsonProperty("image_base64") String imageBase64) {
}
