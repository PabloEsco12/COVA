import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // On utilise le router défini dans src/router/index.js

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import 'bootstrap-icons/font/bootstrap-icons.css'
import '@/assets/custom.css'
import 'animate.css/animate.min.css'
import axios from 'axios'

// Normalize API base URLs from env and rewrite any legacy hardcoded URLs
const __apiBase = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')
const __backendBase = __apiBase.replace(/\/api$/, '') || ''
axios.interceptors.request.use((config) => {
  try {
    const url = typeof config.url === 'string' ? config.url : ''
    if (!url) return config
    // If pointing to localhost:5000 without '/api', redirect to API base
    if (/^http:\/\/localhost:5000\/(?!api\/)/.test(url)) {
      const rest = url.replace(/^http:\/\/localhost:5000\//, '')
      config.url = `${__apiBase}/${rest}`.replace(/\/+$/, '').replace(/([^:])\/\/+/, '$1/')
    } else {
      // Rewrite old localhost API base to env API URL
      config.url = url
        .replace(/^http:\/\/localhost:5000\/api(?=\/|$)/, __apiBase)
        .replace(/^http:\/\/localhost:5000(?=\/|$)/, __backendBase || 'http://localhost:5000')
    }
    return config
  } catch {
    return config
  }
})

// Apply initial theme early to avoid FOUC
try {
  const saved = localStorage.getItem('theme')
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  const dark = saved ? saved === 'dark' : prefersDark
  document.body.classList.toggle('dark-mode', dark)
  document.body.classList.toggle('light-mode', !dark)
} catch {
  document.body.classList.add('light-mode')
}

createApp(App)
  .use(router)
  .mount('#app')
