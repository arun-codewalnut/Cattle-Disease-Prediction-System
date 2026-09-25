import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // The container runs the dev server, so Railway's public hostname has to be allowed
  // explicitly — Vite rejects unknown Host headers otherwise.
  server: {
    allowedHosts: ['.up.railway.app'],
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.js',
  },
})
