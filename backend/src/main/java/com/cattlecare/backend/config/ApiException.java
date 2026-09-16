package com.cattlecare.backend.config;

import org.springframework.http.HttpStatus;

/**
 * Throw this from services/clients to produce a structured {@link ApiError} response —
 * see docs/API_CONTRACTS.md. Prefer this over letting a raw exception fall through to the
 * generic handler.
 */
public class ApiException extends RuntimeException {

    private final String code;
    private final HttpStatus status;

    public ApiException(String code, String message, HttpStatus status) {
        super(message);
        this.code = code;
        this.status = status;
    }

    public String getCode() {
        return code;
    }

    public HttpStatus getStatus() {
        return status;
    }
}
