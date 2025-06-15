import { createApp } from 'vue'
import App from './App.vue'
import { createRouter, createWebHistory } from 'vue-router'
import Login from './components/Login.vue'
import Register from './components/Register.vue'
import Dashboard from './components/Dashboard.vue'
import DashboardHome from './components/DashboardHome.vue'
import Messages from './components/Messages.vue'
import Contacts from './components/Contacts.vue'
import Devices from './components/Devices.vue'
import Profile from './components/Profile.vue'
import Settings from './components/Settings.vue'

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import 'bootstrap-icons/font/bootstrap-icons.css'
import '@/assets/custom.css'

const routes = [
  { path: '/', component: Login },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  {
    path: '/dashboard',
    component: Dashboard,
    children: [
      { path: '', component: DashboardHome },          // /dashboard
      { path: 'messages', component: Messages },        // /dashboard/messages
      { path: 'contacts', component: Contacts },        // /dashboard/contacts
      { path: 'devices', component: Devices },          // /dashboard/devices
      { path: 'profile', component: Profile },          // /dashboard/profile
      { path: 'settings', component: Settings },        // /dashboard/settings
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

createApp(App).use(router).mount('#app')
