package com.cattlecare.backend.config;

import java.util.LinkedHashMap;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.FieldError;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.multipart.support.MissingServletRequestPartException;
import org.springframework.web.servlet.resource.NoResourceFoundException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ApiError> handleApiException(ApiException ex) {
        ApiError error = new ApiError(ex.getCode(), ex.getMessage(), null);
        return ResponseEntity.status(ex.getStatus()).body(error);
    }

    // Thrown by @Valid on a @RequestBody DTO (e.g. a null species) — previously fell
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

    // Found during full-scenario testing: a request to the multipart image endpoint with no
    // multipart parts at all (some HTTP clients send plain form-urlencoded instead of
    // multipart when there's nothing to attach) doesn't reach MissingServletRequestPartException
    // above — Spring rejects the content type itself, before parameter binding runs, and that
    // used to fall through to the catch-all below as a 500 leaking
    // "Content-Type '...' is not supported". Same raw-exception-leak bug class as the handlers
    // above; mapped to the same IMAGE_REQUIRED code since the practical cause is the same
    // (nothing usable was attached). A real browser's multipart form submission never hits
    // this — reproduced only by calling the API directly with a malformed request.
    @ExceptionHandler(HttpMediaTypeNotSupportedException.class)
    public ResponseEntity<ApiError> handleUnsupportedMediaType(HttpMediaTypeNotSupportedException ex) {
        ApiError error = new ApiError("IMAGE_REQUIRED", "An image file is required.", null);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    // Malformed JSON, or a value that doesn't fit the target type — e.g. an invalid
    // `species` string for the Species enum (M11 is the first field that can actually
    // trigger this). Same class of bug as MethodArgumentNotValidException above: without
    // this handler, Jackson's raw deserialization exception would leak through the generic
    // catch-all instead of a clean {code, message, details}.
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ResponseEntity<ApiError> handleUnreadableRequestBody(HttpMessageNotReadableException ex) {
        ApiError error = new ApiError(
                "INVALID_REQUEST_BODY", "Request body is malformed or contains an invalid value.", null);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    // The multipart image endpoint takes `species` as a form field, not JSON, so neither of
    // the two handlers above fires for it: a missing part throws
    // MissingServletRequestParameterException and an unparseable enum value throws
    // MethodArgumentTypeMismatchException. Both used to reach the catch-all below as a 500.
    // Mapped here so the multipart path returns the same codes/statuses as the JSON path —
    // see docs/specs/remove-animal-identity.md.
    @ExceptionHandler(MissingServletRequestParameterException.class)
    public ResponseEntity<ApiError> handleMissingRequestParameter(MissingServletRequestParameterException ex) {
        ApiError error = new ApiError(
                "VALIDATION_FAILED",
                "Request failed validation.",
                Map.of(ex.getParameterName(), "must not be null"));
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public ResponseEntity<ApiError> handleTypeMismatch(MethodArgumentTypeMismatchException ex) {
        ApiError error = new ApiError(
                "INVALID_REQUEST_BODY", "Request body is malformed or contains an invalid value.", null);
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error);
    }

    // An unmapped path used to fall through to the catch-all below as a 500 whose message
    // leaked Spring's internals ("No static resource api/animals for request ..."). That's
    // wrong on both counts — nothing broke, the route just isn't there — and it started
    // mattering once /api/animals* was removed, since any old client still calling it lands
    // here. See docs/specs/remove-animal-identity.md.
    @ExceptionHandler(NoResourceFoundException.class)
    public ResponseEntity<ApiError> handleNoResourceFound(NoResourceFoundException ex) {
        ApiError error = new ApiError("NOT_FOUND", "No endpoint exists at this path.", null);
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiError> handleUnexpected(Exception ex) {
        ApiError error = new ApiError("INTERNAL_ERROR", ex.getMessage(), null);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(error);
    }
}
