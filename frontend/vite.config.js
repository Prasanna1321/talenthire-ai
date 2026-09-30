import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Belongs in: frontend/vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Lets the frontend call /api/... during dev without CORS friction
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
