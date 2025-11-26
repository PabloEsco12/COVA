// Configuration Vite pour la SPA (aliases + support custom element emoji-picker)
// Inclut vueDevTools pour le debug et un alias @ vers /src
import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // Autoriser le composant web emoji-picker sans warning
          isCustomElement: tag => tag === 'emoji-picker',
        },
      },
    }),
    vueDevTools(),
  ],
  resolve: {
    alias: {
      // Raccourci @ -> /src pour des imports plus lisibles
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
})
