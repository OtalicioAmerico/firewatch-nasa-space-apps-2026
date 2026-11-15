import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// Mockup 06A: no proxy, no API, no network data sources. maplibre-gl is not pre-bundled (worker resolution).
export default defineConfig({
  plugins: [react()],
  optimizeDeps: { exclude: ['maplibre-gl'] },
  server: { host: '127.0.0.1', port: 5173 },
})
