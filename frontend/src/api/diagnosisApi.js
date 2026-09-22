import { apiPost, apiPostMultipart } from './client'

// One call per diagnosis. This used to be two — create an animal record, then post a
// diagnosis against its id — but animal identity (tag number, farm ID, the record itself)
// was removed since none of it reached the model. See docs/specs/remove-animal-identity.md.

export function submitSymptoms(species, symptoms, correlationId) {
  return apiPost('/api/diagnoses', { species, symptoms }, correlationId)
}

export function submitImage(species, imageFiles, correlationId) {
  const formData = new FormData()
  // species travels as a form field here, not JSON — this endpoint is multipart.
  formData.append('species', species)
  imageFiles.forEach((file) => formData.append('images', file))
  return apiPostMultipart('/api/diagnoses/image', formData, correlationId)
}
