package com.cattlecare.backend.cattle.dto;

import java.time.Instant;

import com.cattlecare.backend.cattle.Cattle;

public record CattleResponse(Long id, String tagNumber, Long farmId, Instant createdAt) {

    public static CattleResponse from(Cattle cattle) {
        return new CattleResponse(cattle.getId(), cattle.getTagNumber(), cattle.getFarmId(), cattle.getCreatedAt());
    }
}
