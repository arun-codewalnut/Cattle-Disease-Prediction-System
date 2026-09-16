package com.cattlecare.backend.config;

import java.util.Map;

/**
 * Standard error response shape shared across `backend` and `ml-service`.
 * See docs/API_CONTRACTS.md — don't change this shape without updating that doc.
 */
public record ApiError(String code, String message, Map<String, Object> details) {
}
