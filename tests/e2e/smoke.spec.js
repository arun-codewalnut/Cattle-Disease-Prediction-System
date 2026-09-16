import { expect, test } from '@playwright/test'

// Full-stack smoke test — confirms all three services are up and reachable together.
// Run after `make up` (or `docker compose up`) from this directory: `npx playwright test`.

const FRONTEND_URL = process.env.FRONTEND_URL ?? 'http://localhost:5173'
const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8080'
const ML_SERVICE_URL = process.env.ML_SERVICE_URL ?? 'http://localhost:8000'

test('backend health check responds', async ({ request }) => {
  const response = await request.get(`${BACKEND_URL}/actuator/health`)
  expect(response.ok()).toBeTruthy()
  const body = await response.json()
  expect(body.status).toBe('UP')
})

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

test('frontend loads', async ({ page }) => {
  await page.goto(FRONTEND_URL)
  await expect(page.getByRole('heading', { name: /get started/i })).toBeVisible()
})
