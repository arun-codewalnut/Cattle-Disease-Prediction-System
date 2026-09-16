package com.cattlecare.backend.cattle;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.Optional;

import org.junit.jupiter.api.Test;
import org.springframework.dao.DataIntegrityViolationException;

import com.cattlecare.backend.config.ApiException;

class CattleServiceTest {

    private final CattleRepository cattleRepository = mock(CattleRepository.class);
    private final CattleService cattleService = new CattleService(cattleRepository);

    @Test
    void create_savesAndReturnsCattle() {
        Cattle saved = new Cattle("COW-001", 42L);
        when(cattleRepository.save(any())).thenReturn(saved);

        Cattle result = cattleService.create("COW-001", 42L);

        assertEquals("COW-001", result.getTagNumber());
        assertEquals(42L, result.getFarmId());
    }

    @Test
    void create_duplicateTag_throwsApiExceptionWithConflict() {
        when(cattleRepository.save(any())).thenThrow(new DataIntegrityViolationException("duplicate"));

        ApiException ex = assertThrows(ApiException.class, () -> cattleService.create("COW-001", 42L));
        assertEquals("CATTLE_TAG_DUPLICATE", ex.getCode());
    }

    @Test
    void getOrThrow_found_returnsCattle() {
        Cattle cattle = new Cattle("COW-001", 42L);
        when(cattleRepository.findById(1L)).thenReturn(Optional.of(cattle));

        assertSame(cattle, cattleService.getOrThrow(1L));
    }

    @Test
    void getOrThrow_notFound_throwsApiExceptionWithNotFound() {
        when(cattleRepository.findById(999L)).thenReturn(Optional.empty());

        ApiException ex = assertThrows(ApiException.class, () -> cattleService.getOrThrow(999L));
        assertEquals("CATTLE_NOT_FOUND", ex.getCode());
    }
}
