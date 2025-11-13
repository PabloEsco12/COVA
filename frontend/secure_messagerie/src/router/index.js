// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'

// pages publiques
import LoginView from '@/views/LoginView.vue'
import LoginTotpView from '@/views/LoginTotpView.vue'
import RegisterView from '../views/RegisterView.vue'
import ResetPasswordView from '@/views/ResetPasswordView.vue'
import NewPasswordView from '@/views/NewPasswordView.vue'
import ConfirmEmailView from '@/views/ConfirmEmailView.vue'

// layout / dashboard
import Dashboard from '../components/Dashboard.vue'
import DashboardHome from '../components/DashboardHomeEnhanced.vue'
import Messages from '@/views/MessagesView.vue'
import NewConversationForm from '@/components/messages/new/NewConversationForm.vue'
import ContactsView from '@/views/ContactsView.vue'
import DevicesView from '@/views/DevicesView.vue'
import SettingsView from '@/views/SettingsView.vue'

const routes = [
  { path: '/', redirect: '/login' },

  { path: '/login', name: 'login', component: LoginView },
  { path: '/login/totp', name: 'login-totp', component: LoginTotpView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/reset-password', name: 'reset-password', component: ResetPasswordView },
  { path: '/new-password', name: 'new-password', component: NewPasswordView },

  // ✅ on accepte les 2 URLs possibles venant du mail
  { path: '/confirm/:token', name: 'confirm-email', component: ConfirmEmailView },
  { path: '/confirm-email/:token', name: 'confirm-email-alt', component: ConfirmEmailView },

  {
    path: '/dashboard',
    component: Dashboard,
    children: [
      { path: '', name: 'dashboard-home', component: DashboardHome },
      { path: 'messages/new', name: 'dashboard-new-conversation', component: NewConversationForm },
      { path: 'messages', name: 'dashboard-messages', component: Messages },
      { path: 'contacts', name: 'dashboard-contacts', component: ContactsView },
      { path: 'devices', name: 'dashboard-devices', component: DevicesView },
      { path: 'settings', name: 'dashboard-settings', component: SettingsView },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// garde de navigation
router.beforeEach((to, from, next) => {
  const publicPages = [
    '/login',
    '/login/totp',
    '/register',
    '/reset-password',
    '/new-password',
  ]

  const isPublic =
    publicPages.includes(to.path) ||
    // ✅ on autorise aussi les 2 variantes
    to.path.startsWith('/confirm/') ||
    to.path.startsWith('/confirm-email/')

  const isDashboard = to.path.startsWith('/dashboard')
  const loggedIn = !!localStorage.getItem('access_token')

  if (isDashboard && !loggedIn && !isPublic) {
    return next('/login')
  }

  next()
})

export default router
