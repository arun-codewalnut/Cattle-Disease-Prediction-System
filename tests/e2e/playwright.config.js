import { existsSync } from 'node:fs'
import { defineConfig } from '@playwright/test'

// Optional local overrides (FRONTEND_URL, ML_SERVICE_URL) — see .env.example. Node's own
// loader, so no extra dependency; values already set in the shell win.
if (existsSync('.env')) process.loadEnvFile('.env')

export default defineConfig({
  testDir: '.',
  timeout: 30_000,
  fullyParallel: true,
  reporter: 'list',
  use: {
    trace: 'retain-on-failure',
  },
})
