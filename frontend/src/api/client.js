// Shared fetch wrapper — every backend call goes through here so there's exactly one
// error-handling path, per frontend/AGENTS.md's convention.

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8080'

export class ApiError extends Error {
  constructor(code, message, details) {
    super(message)
    this.code = code
    this.details = details
  }
}

export async function apiPost(path, body, correlationId) {
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-Id': correlationId,
      },
      body: JSON.stringify(body),
    })
  } catch {
    throw new ApiError('NETWORK_ERROR', 'Could not reach the server. Check your connection and try again.', null)
  }

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    if (payload && typeof payload.code === 'string') {
      throw new ApiError(payload.code, payload.message ?? 'Something went wrong.', payload.details ?? null)
    }
    throw new ApiError('UNKNOWN_ERROR', `Request failed with status ${response.status}.`, null)
  }

  return payload
}
