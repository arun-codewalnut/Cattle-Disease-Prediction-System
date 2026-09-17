import { apiPost } from './client'

export function createCattle({ tagNumber, farmId }, correlationId) {
  return apiPost('/api/cattle', { tagNumber, farmId: Number(farmId) }, correlationId)
}

export function submitSymptoms(cattleId, symptoms, correlationId) {
  return apiPost(`/api/cattle/${cattleId}/diagnoses`, { symptoms }, correlationId)
}
