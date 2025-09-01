import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/graphql/': { target: 'https://comments-backend-755819237934.europe-central2.run.app', changeOrigin: true, ws: true },
      '/api/':     { target: 'https://comments-backend-755819237934.europe-central2.run.app', changeOrigin: true },
      '/media/':   { target: 'https://comments-backend-755819237934.europe-central2.run.app', changeOrigin: true },
    },
  },
})
