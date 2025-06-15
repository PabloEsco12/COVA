// src/router/index.js

import { createRouter, createWebHistory } from 'vue-router'
import Login from '../components/Login.vue'
import Register from '../components/Register.vue'
import Dashboard from '../components/Dashboard.vue'
import DashboardHome from '../components/DashboardHome.vue'
import Messages from '../components/Messages.vue'
import Contacts from '../components/Contacts.vue'
import Profile from '../components/Profile.vue'
// Ajoute les autres imports si besoin

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  {
    path: '/dashboard',
    component: Dashboard,
    children: [
      { path: '', component: DashboardHome }, // /dashboard
      { path: 'messages', component: Messages },
      { path: 'contacts', component: Contacts },
      { path: 'profile', component: Profile },
      // Ajoute d'autres routes enfants ici (devices, settings, etc)
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// PROTECTION : Interdit d'aller sur /dashboard si pas connecté
router.beforeEach((to, from, next) => {
  const publicPages = ['/login', '/register']
  const authRequired = !publicPages.includes(to.path) && to.path.startsWith('/dashboard')
  const loggedIn = !!localStorage.getItem('access_token')

  if (authRequired && !loggedIn) {
    return next('/login')
  }
  next()
})

export default router
