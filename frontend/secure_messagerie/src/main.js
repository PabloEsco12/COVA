import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // On utilise le router défini dans src/router/index.js

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import 'bootstrap-icons/font/bootstrap-icons.css'
import '@/assets/custom.css'
import 'animate.css/animate.min.css'

createApp(App)
  .use(router)
  .mount('#app')
