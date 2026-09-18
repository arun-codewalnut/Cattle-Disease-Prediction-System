package com.cattlecare.backend.config;

import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.multipart.support.MissingServletRequestPartException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ApiError> handleApiException(ApiException ex) {
        ApiError error = new ApiError(ex.getCode(), ex.getMessage(), null);
        return ResponseEntity.status(ex.getStatus()).body(error);
    }

    // Thrown by @Valid on a @RequestBody DTO (e.g. a blank tagNumber) — previously fell
    // through to the generic handler below, which dumped the raw exception (including every
    // internal class/code name) as the user-facing "message". Maps each rejected field to a
    // short, readable reason instead.
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiError> handleValidationFailure(MethodArgumentNotValidException ex) {
        Map<String, Object> fieldErrors = new LinkedHashMap<>();
        for (FieldError fieldError : ex.getBindingResult().getFieldErrors()) {
            fieldErrors.put(fieldError.getField(), fieldError.getDefaultMessage());
        }
        ApiError error = new ApiError("VALIDATION_FAILED", "Request failed validation.", fieldErrors);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    // Thrown by Spring itself, before DiagnosisService's own size check runs, whenever a
    // multipart upload exceeds spring.servlet.multipart.max-file-size/max-request-size —
    // mapped to the same IMAGE_TOO_LARGE code so callers see one consistent error either way.
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<ApiError> handleMaxUploadSizeExceeded(MaxUploadSizeExceededException ex) {
        ApiError error = new ApiError("IMAGE_TOO_LARGE", "Uploaded file exceeds the size limit.", null);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    @ExceptionHandler(MissingServletRequestPartException.class)
    public ResponseEntity<ApiError> handleMissingPart(MissingServletRequestPartException ex) {
        ApiError error = new ApiError("IMAGE_REQUIRED", "An image file is required.", null);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> handleUnexpected(Exception ex) {
        ApiError error = new ApiError("INTERNAL_ERROR", ex.getMessage(), null);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}
