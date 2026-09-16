package com.cattlecare.backend.cattle;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import com.cattlecare.backend.cattle.dto.CattleResponse;
import com.cattlecare.backend.cattle.dto.CreateCattleRequest;
import jakarta.validation.Valid;

@RestController
public class CattleController {

    private final CattleService cattleService;

    public CattleController(CattleService cattleService) {
        this.cattleService = cattleService;
    }

    @PostMapping("/api/cattle")
    public ResponseEntity<CattleResponse> create(@Valid @RequestBody CreateCattleRequest request) {
        Cattle cattle = cattleService.create(request.tagNumber(), request.farmId());
        return ResponseEntity.status(HttpStatus.CREATED).body(CattleResponse.from(cattle));
    }
}
