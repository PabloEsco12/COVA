// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/Login.vue'
import Register from '../components/Register.vue'
import Dashboard from '../components/Dashboard.vue'
import DashboardHome from '../components/DashboardHome.vue'
import Messages from '../components/Messages.vue'
import Contacts from '../components/Contacts.vue'
import Invitations from '../components/Invitations.vue'
import Profile from '../components/Profile.vue'
import ResetPassword from '../components/ResetPassword.vue'
import NewPassword from '../components/NewPassword.vue'
import ConfirmEmail from '../components/ConfirmEmail.vue'
import Devices from '../components/Devices.vue'
import Settings from '../components/Settings.vue'
// Ajoute ici Devices, Settings, etc si tu les crées

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/reset-password', component: ResetPassword },
  { path: '/new-password', component: NewPassword },
  {
    path: '/dashboard',
    component: Dashboard,
    children: [
      { path: '', component: DashboardHome }, // /dashboard
      { path: 'messages', component: Messages }, // /dashboard/messages
      { path: 'contacts', component: Contacts }, // /dashboard/contacts
      { path: 'invitations', component: Invitations }, // /dashboard/invitations
      { path: 'profile', component: Profile }, // /dashboard/profile
      { path: 'devices', component: Devices }, // /dashboard/devices
      { path: 'settings', component: Settings }, // /dashboard/settings      
      { path: '/confirm-email/:token', component: ConfirmEmail },
      // Tu peux ajouter ici { path: 'devices', component: Devices }, etc.
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Interdiction d’accès au dashboard si non connecté
router.beforeEach((to, from, next) => {
  const publicPages = ['/login', '/register', '/reset-password', '/new-password']
  const isPublic = publicPages.includes(to.path) || to.path.startsWith('/confirm-email')
  const isDashboard = to.path.startsWith('/dashboard')
  const loggedIn = !!localStorage.getItem('access_token')

  if (isDashboard && !loggedIn) {
    return next('/login')
  }
  next()
})

export default router
