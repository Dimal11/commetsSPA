// vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/graphql': { target: 'http://127.0.0.1:8000', changeOrigin: true, ws: true },
      '/api':     { target: 'http://127.0.0.1:8000', changeOrigin: true },
      '/media':   { target: 'http://127.0.0.1:8000', changeOrigin: true },
    },
  },
})
