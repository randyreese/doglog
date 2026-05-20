import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  base: '/doglog/',
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/doglog/dogs': 'http://127.0.0.1:8001',
      '/doglog/events': 'http://127.0.0.1:8001',
      '/doglog/status': 'http://127.0.0.1:8001',
      '/doglog/health': 'http://127.0.0.1:8001',
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
        icons: [
          { src: '/doglog/icons/doglog-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/doglog/icons/doglog-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        navigateFallback: '/doglog/index.html',
      },
    }),
  ],
})
