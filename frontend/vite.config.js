import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// The Flask API runs on port 5001 (macOS uses 5000 for AirPlay Receiver).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:5001',
    },
  },
})
