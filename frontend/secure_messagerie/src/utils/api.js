// ===== API Utility =====
// Point central pour preparer les appels HTTP (URLs normalisees, token, redirections) afin d'offrir un comportement coherent partout.
import axios from 'axios'
import router from '@/router'
import { clearSession, hasStoredSession } from '@/services/auth'

// ---- Construction des URLs backend ----
// Garantit que l'URL de base se termine toujours par "/api" peu importe la configuration fournie.
const raw = (import.meta.env.VITE_API_URL || 'http://localhost:5000/api').toString().replace(/\/+$/, '')
const apiBase = raw.endsWith('/api') ? raw : `${raw}/api`
const backendBase = apiBase.replace(/\/api$/, '')

// ---- Client Axios partage ----
// Utilisé partout dans l'app pour éviter de répéter la configuration commune.
const api = axios.create({ baseURL: apiBase })
const AUTH_EXEMPT_ENDPOINTS = [
  '/auth/login',
  '/auth/register',
  '/auth/resend-confirmation',
  '/auth/forgot-password',
  '/auth/reset-password',
]

// ---- Normalisation des chemins ----
// Convertit une URL relative/absolue en chemin canonique (sans query/hash) pour comparer avec les endpoints proteges.
function normalizeRequestedPath(config) {
  const target = config?.url || ''
  if (!target) return ''
  try {
    const base = config?.baseURL || apiBase
    const absolute = new URL(target, base)
    return absolute.pathname.replace(/\/+$/, '') || '/'
  } catch {
    const pathOnly = target.split('?')[0].split('#')[0]
    if (!pathOnly) return ''
    const prefixed = pathOnly.startsWith('/') ? pathOnly : `/${pathOnly}`
    return prefixed.replace(/\/+$/, '') || '/'
  }
}

// ---- Exemptions d'auth ----
// Permet de laisser passer les endpoints publics sans forcer un token, même si un ancien token est stocké.
function isAuthExemptRequest(config) {
  const rawPath = normalizeRequestedPath(config)
  if (!rawPath) return false
  const stripped =
    rawPath === '/api'
      ? '/'
      : rawPath.startsWith('/api/')
        ? rawPath.slice(4)
        : rawPath
  const canonical = stripped.startsWith('/') ? stripped : `/${stripped}`
  return AUTH_EXEMPT_ENDPOINTS.includes(canonical)
}

// ---- Intercepteur requete ----
// Injecte silencieusement le token s'il existe dans le localStorage sans bloquer la requete en cas d'erreur.
api.interceptors.request.use((config) => {
  try {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers = config.headers || {}
      if (!config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
  } catch {}
  return config
})

let handlingAuthFailure = false
// ---- Intercepteur reponse ----
// Surveille les 401/403 : nettoie la session, choisit la raison et redirige vers /login pour eviter les boucles.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detailRaw = error.response?.data?.detail || error.response?.data?.error || ''
    const detail = typeof detailRaw === 'string' ? detailRaw.toLowerCase() : ''
    const requiresTotp = Boolean(error.response?.data?.require_totp)
    const hadAuthHeader =
      typeof error.config?.headers?.Authorization === 'string' &&
      error.config.headers.Authorization.toLowerCase().startsWith('bearer ')
    const authExempt = isAuthExemptRequest(error.config)
    const hasSession = hadAuthHeader || hasStoredSession()
    const shouldForceLogout =
      !requiresTotp &&
      !authExempt &&
      hasSession &&
      (status === 401 ||
        (status === 403 && (detail.includes('token') || detail.includes('credential'))))

    if (shouldForceLogout && !handlingAuthFailure) {
      handlingAuthFailure = true
      try {
        clearSession()
      } catch {}
      const reason =
        detail.includes('expired') || detail.includes('expired token')
          ? 'session-expired'
          : 'invalid-token'

      const redirectToLogin = () => {
        const currentPath = router?.currentRoute?.value?.path
        if (currentPath !== '/login') {
          router
            .push({ path: '/login', query: { reason } })
            .catch(() => {
              if (typeof window !== 'undefined') {
                window.location.href = `/login?reason=${reason}`
              }
            })
        } else if (typeof window !== 'undefined') {
          window.location.href = `/login?reason=${reason}`
        }
      }

      redirectToLogin()
      setTimeout(() => {
        handlingAuthFailure = false
      }, 1500)
    }

    return Promise.reject(error)
  },
)

export { api, apiBase, backendBase }
