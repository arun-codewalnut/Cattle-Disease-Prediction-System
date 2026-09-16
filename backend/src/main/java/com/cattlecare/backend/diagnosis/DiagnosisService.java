package com.cattlecare.backend.diagnosis;

import java.util.Map;

import org.slf4j.MDC;
import org.springframework.stereotype.Service;

import com.cattlecare.backend.cattle.Cattle;
import com.cattlecare.backend.cattle.CattleService;
import com.cattlecare.backend.client.DiagnosisResult;
import com.cattlecare.backend.client.MlServiceClient;
import com.cattlecare.backend.config.CorrelationIdFilter;
import com.cattlecare.backend.diagnosis.dto.DiagnosisCaseResponse;

@Service
public class DiagnosisService {

    private final CattleService cattleService;
    private final MlServiceClient mlServiceClient;
    private final DiagnosisCaseRepository diagnosisCaseRepository;

    public DiagnosisService(
            CattleService cattleService,
            MlServiceClient mlServiceClient,
            DiagnosisCaseRepository diagnosisCaseRepository) {
        this.cattleService = cattleService;
        this.mlServiceClient = mlServiceClient;
        this.diagnosisCaseRepository = diagnosisCaseRepository;
    }

    public DiagnosisCaseResponse submitSymptoms(Long cattleId, Map<String, Object> symptoms) {
        Cattle cattle = cattleService.getOrThrow(cattleId);

        // If this throws (unreachable / error response), nothing gets persisted below —
        // we don't record a case that never actually got a diagnosis.
        DiagnosisResult result = mlServiceClient.diagnose(symptoms, null);

        String correlationId = MDC.get(CorrelationIdFilter.MDC_KEY);
        DiagnosisCase entity = new DiagnosisCase(
                cattle.getId(),
                correlationId,
                symptoms,
                result.diagnosis(),
                result.confidence(),
                result.recommendedAction());
        diagnosisCaseRepository.save(entity);

        return DiagnosisCaseResponse.from(entity, result.explanation());
    }
}
