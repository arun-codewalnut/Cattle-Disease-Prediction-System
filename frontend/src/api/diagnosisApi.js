import { apiPost, apiPostMultipart } from './client'

export function createAnimal({ tagNumber, farmId, species }, correlationId) {
  return apiPost('/api/animals', { tagNumber, farmId: Number(farmId), species }, correlationId)
}

export function submitSymptoms(animalId, symptoms, correlationId) {
  return apiPost(`/api/animals/${animalId}/diagnoses`, { symptoms }, correlationId)
}

export function submitImage(animalId, imageFiles, correlationId) {
  const formData = new FormData()
  imageFiles.forEach((file) => formData.append('images', file))
  return apiPostMultipart(`/api/animals/${animalId}/diagnoses/image`, formData, correlationId)
}
