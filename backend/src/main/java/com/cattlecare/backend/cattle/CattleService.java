package com.cattlecare.backend.cattle;

import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

import com.cattlecare.backend.config.ApiException;

@Service
public class CattleService {

    private final CattleRepository cattleRepository;

    public CattleService(CattleRepository cattleRepository) {
        this.cattleRepository = cattleRepository;
    }

    public Cattle create(String tagNumber, Long farmId) {
        try {
            return cattleRepository.save(new Cattle(tagNumber, farmId));
        } catch (DataIntegrityViolationException ex) {
            throw new ApiException(
                    "CATTLE_TAG_DUPLICATE",
                    "A cattle record with tag number '" + tagNumber + "' already exists",
                    HttpStatus.CONFLICT);
        }
    }

    /** Throws {@link ApiException} (CATTLE_NOT_FOUND, 404) rather than returning null/Optional
     * — every caller needs the same not-found handling, so centralize it here. */
    public Cattle getOrThrow(Long cattleId) {
        return cattleRepository.findById(cattleId)
                .orElseThrow(() -> new ApiException(
                        "CATTLE_NOT_FOUND",
                        "No cattle found with id " + cattleId,
                        HttpStatus.NOT_FOUND));
    }
}
