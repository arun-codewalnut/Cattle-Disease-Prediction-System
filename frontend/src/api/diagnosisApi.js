import { apiPost, apiPostMultipart } from './client'

export function createCattle({ tagNumber, farmId }, correlationId) {
  return apiPost('/api/cattle', { tagNumber, farmId: Number(farmId) }, correlationId)
}

export function submitSymptoms(cattleId, symptoms, correlationId) {
  return apiPost(`/api/cattle/${cattleId}/diagnoses`, { symptoms }, correlationId)
}

export function submitImage(cattleId, imageFile, correlationId) {
  const formData = new FormData()
  formData.append('image', imageFile)
  return apiPostMultipart(`/api/cattle/${cattleId}/diagnoses/image`, formData, correlationId)
}
