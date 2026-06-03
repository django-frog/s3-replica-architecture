import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // Whitelist your custom Split-Horizon DNS domain
    allowedHosts: ['vault.local']
  }
})
