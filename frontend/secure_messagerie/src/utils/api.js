import axios from 'axios'
import router from '@/router'
import { clearSession } from '@/services/auth'

// Normalize API base so it always ends with '/api' (no trailing slash after)
const raw = (import.meta.env.VITE_API_URL || 'http://localhost:5000/api').toString().replace(/\/+$/, '')
const apiBase = raw.endsWith('/api') ? raw : `${raw}/api`
const backendBase = apiBase.replace(/\/api$/, '')

const api = axios.create({ baseURL: apiBase })

// Attach token automatically if present (non-blocking)
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
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status
    const detailRaw = error.response?.data?.detail || error.response?.data?.error || ''
    const detail = typeof detailRaw === 'string' ? detailRaw.toLowerCase() : ''
    const shouldForceLogout =
      status === 401 ||
      (status === 403 && (detail.includes('token') || detail.includes('credential')))

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
