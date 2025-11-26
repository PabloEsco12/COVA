// src/router/index.js
// Configuration centrale du router Vue : routes publiques/privees et garde d'acces
import { createRouter, createWebHistory } from 'vue-router'
import { clearSession, getAccessToken, hasStoredSession, isAccessTokenExpired } from '@/services/auth'

// Pages publiques (authentification, reset, confirmation)
import LoginView from '@/views/LoginView.vue'
import LoginTotpView from '@/views/LoginTotpView.vue'
import RegisterView from '../views/RegisterView.vue'
import ResetPasswordView from '@/views/ResetPasswordView.vue'
import NewPasswordView from '@/views/NewPasswordView.vue'
import ConfirmEmailView from '@/views/ConfirmEmailView.vue'

// Layout / dashboard
import Dashboard from '@/components/dashboard/Dashboard.vue'
import DashboardHome from '@/components/dashboard/DashboardHomeEnhanced.vue'
import Messages from '@/views/MessagesView.vue'
import NewConversationForm from '@/components/messages/new/NewConversationForm.vue'
import ContactsView from '@/views/ContactsView.vue'
import DevicesView from '@/views/DevicesView.vue'
import SettingsView from '@/views/SettingsView.vue'
import AdminUsersView from '@/views/AdminUsersView.vue'
import FaqView from '@/views/FaqView.vue'

const routes = [
  { path: '/', redirect: '/login' },

  { path: '/login', name: 'login', component: LoginView },
  { path: '/login/totp', name: 'login-totp', component: LoginTotpView },
  { path: '/register', name: 'register', component: RegisterView },
  { path: '/reset-password', name: 'reset-password', component: ResetPasswordView },
  { path: '/new-password', name: 'new-password', component: NewPasswordView },

  // Alias de routes de confirmation pour couvrir les liens d'email legacy/actuels
  //  on accepte les 2 URLs possibles venant du mail
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
      { path: 'admin', name: 'dashboard-admin-users', component: AdminUsersView },
      { path: 'faq', name: 'dashboard-faq', component: FaqView },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Garde de navigation : force une session valide pour les routes dashboard
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
    // Autoriser aussi les 2 variantes de lien de confirmation
    to.path.startsWith('/confirm/') ||
    to.path.startsWith('/confirm-email/')

  const isDashboard = to.path.startsWith('/dashboard')
  const loggedIn = hasStoredSession()
  const token = getAccessToken()
  const expired = loggedIn && (!token || isAccessTokenExpired(token))

  if (expired) {
    clearSession()
    if (!isPublic) {
      return next({ path: '/login', query: { reason: 'session-expired' } })
    }
  } else if (isDashboard && !loggedIn && !isPublic) {
    return next('/login')
  }

  next()
})

export default router
