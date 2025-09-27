import axios from 'axios'

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

export { api, apiBase, backendBase }

