import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // On utilise le router défini dans src/router/index.js

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import 'bootstrap-icons/font/bootstrap-icons.css'
import '@/assets/custom.css'
import 'animate.css/animate.min.css'

// Apply initial theme early to avoid FOUC
try {
  const saved = localStorage.getItem('theme')
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  const dark = saved ? saved === 'dark' : prefersDark
  if (dark) document.body.classList.add('dark-mode')
} catch {}

createApp(App)
  .use(router)
  .mount('#app')
