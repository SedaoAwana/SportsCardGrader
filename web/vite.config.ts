import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Dev only: forward API calls to the FastAPI server so the app works
    // on http://localhost:5173 without setting VITE_API_URL.
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
