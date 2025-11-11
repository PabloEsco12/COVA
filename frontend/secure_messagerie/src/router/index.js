// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/Login.vue'
import LoginTotp from '../components/LoginTotp.vue'
import RegisterView from '../views/RegisterView.vue'
import Dashboard from '../components/Dashboard.vue'
import DashboardHome from '../components/DashboardHomeEnhanced.vue'
import Messages from '../components/MessagesRealtimeNew.vue'
import NewConversation from '../components/NewConversation.vue'
import ContactsView from '@/views/ContactsView.vue'
import ResetPassword from '../components/ResetPassword.vue'
import NewPassword from '../components/NewPassword.vue'
import ConfirmEmailView from '@/views/ConfirmEmailView.vue'
import DevicesView from '@/views/DevicesView.vue'
import SettingsView from '@/views/SettingsView.vue'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/register', component: RegisterView },
  { path: '/login/totp', component: LoginTotp },
  { path: '/reset-password', component: ResetPassword },
  { path: '/new-password', component: NewPassword },
  // confirmation de mail
  { path: '/confirm/:token', component: ConfirmEmailView },

  {
    path: '/dashboard',
    component: Dashboard,
    children: [
      { path: '', component: DashboardHome },               // /dashboard
      { path: 'messages/new', component: NewConversation }, // /dashboard/messages/new
      { path: 'messages', component: Messages },            // /dashboard/messages
      { path: 'contacts', component: ContactsView },        // /dashboard/contacts
      { path: 'devices', component: DevicesView },          // /dashboard/devices
      { path: 'settings', component: SettingsView },        // /dashboard/settings ✅
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// garde de navigation
router.beforeEach((to, from, next) => {
  // pages publiques
  const publicPages = [
    '/login',
    '/login/totp',
    '/register',
    '/reset-password',
    '/new-password',
  ]

  const isPublic =
    publicPages.includes(to.path) ||
    // on autorise aussi /confirm/<token>
    to.path.startsWith('/confirm/')

  const isDashboard = to.path.startsWith('/dashboard')
  const loggedIn = !!localStorage.getItem('access_token')

  if (isDashboard && !loggedIn && !isPublic) {
    return next('/login')
  }
  next()
})

export default router
