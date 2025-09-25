// frontend/vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Add this proxy configuration
    proxy: {
      // Proxy requests from /api to your backend service
      '/api': {
        target: 'http://signconnect-backend-svc.signconnect.svc.cluster.local:8000', // Use the internal Kubernetes service name
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
