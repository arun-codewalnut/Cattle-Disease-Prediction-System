import { expect, test } from '@playwright/test'

// Full-stack smoke test — confirms both services are up and reachable together.
// Run after `make up` (or `docker compose up`) from this directory: `npx playwright test`.

const FRONTEND_URL = process.env.FRONTEND_URL ?? 'http://localhost:5173'
const ML_SERVICE_URL = process.env.ML_SERVICE_URL ?? 'http://localhost:8000'

test('ml-service health check responds', async ({ request }) => {
  const response = await request.get(`${ML_SERVICE_URL}/health`)
  expect(response.ok()).toBeTruthy()
  const body = await response.json()
  expect(body.status).toBe('ok')
})

test('ml-service diagnose endpoint returns the correlation id header', async ({ request }) => {
  const response = await request.post(`${ML_SERVICE_URL}/agent/diagnose`, {
    data: { symptoms: { fever: true } },
  })
  expect(response.ok()).toBeTruthy()
  expect(response.headers()['x-correlation-id']).toBeTruthy()
})

// The endpoint the frontend actually calls (it used to live in the Java backend).
test('public symptom diagnosis endpoint returns a diagnosis', async ({ request }) => {
  const response = await request.post(`${ML_SERVICE_URL}/api/diagnoses`, {
    data: { species: 'COW', symptoms: { fever: true, mouth_lesions: true, excessive_salivation: true } },
  })
  expect(response.status()).toBe(201)
  const body = await response.json()
  expect(body.species).toBe('COW')
  expect(body.recommendedAction).toBeTruthy()
})

test('frontend loads', async ({ page }) => {
  await page.goto(FRONTEND_URL)
  await expect(page.getByRole('heading', { name: /animal health checker/i })).toBeVisible()
})
