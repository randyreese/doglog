import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/doglog/',
  define: {
    __BUILD_TIME__: JSON.stringify(new Date().toISOString()),
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/doglog/dogs': 'http://127.0.0.1:8001',
      '/doglog/events': 'http://127.0.0.1:8001',
      '/doglog/status': 'http://127.0.0.1:8001',
      '/doglog/health': 'http://127.0.0.1:8001',
      '/doglog/meal-slots': 'http://127.0.0.1:8001',
      '/doglog/meal-ingredients': 'http://127.0.0.1:8001',
      '/doglog/meal-logs': 'http://127.0.0.1:8001',
      '/doglog/meal-configs': 'http://127.0.0.1:8001',
      '/doglog/milestones': 'http://127.0.0.1:8001',
      '/doglog/milestone-event-types': 'http://127.0.0.1:8001',
      '/doglog/medication-logs': 'http://127.0.0.1:8001',
      '/doglog/medications': 'http://127.0.0.1:8001',
      '/doglog/medication-names': 'http://127.0.0.1:8001',
      '/doglog/lan-url': 'http://127.0.0.1:8001',
      '/doglog/connect-qr': 'http://127.0.0.1:8001',
    },
  },
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      manifest: {
        name: 'Dog Log',
        short_name: 'DogLog',
        description: 'Daily dog care tracker',
        theme_color: '#5b8dd9',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/doglog/',
        scope: '/doglog/',
        icons: [
          { src: '/doglog/icons/doglog-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/doglog/icons/doglog-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/doglog/icons/doglog.svg', sizes: 'any', type: 'image/svg+xml' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        navigateFallback: '/doglog/index.html',
      },
    }),
  ],
})
