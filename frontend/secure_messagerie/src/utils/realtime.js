const DEFAULT_HTTP_ORIGIN = 'http://localhost:8000'

function stripTrailingSlash(value) {
  return value.replace(/\/+$/, '')
}

function getRuntimeOrigin() {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin
  }
  return DEFAULT_HTTP_ORIGIN
}

function normalizeApiBase(candidate) {
  const raw = (candidate || '').toString().trim()
  if (!raw) return '/api'
  const trimmed = stripTrailingSlash(raw)
  return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`
}

let cachedWsBase = ''

export function resolveWsBase() {
  if (cachedWsBase) return cachedWsBase
  const envWsBase = (import.meta.env?.VITE_WS_BASE || '').toString().trim()
  if (envWsBase) {
    cachedWsBase = stripTrailingSlash(envWsBase)
    return cachedWsBase
  }

  const apiBase = normalizeApiBase(import.meta.env?.VITE_API_URL || '')
  const origin = getRuntimeOrigin()

  try {
    const parsed = new URL(apiBase, origin)
    const protocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:'
    const basePath = stripTrailingSlash(parsed.pathname || '')
    const path = `${basePath || ''}/ws`
    cachedWsBase = `${protocol}//${parsed.host}${path}`.replace(/\/+$/, '')
    return cachedWsBase
  } catch {
    const fallbackOrigin = origin.replace(/^https:/i, 'wss:').replace(/^http:/i, 'ws:')
    cachedWsBase = `${stripTrailingSlash(fallbackOrigin)}/api/ws`
    return cachedWsBase
  }
}

export function buildWsUrl(path = '', query = undefined) {
  const base = stripTrailingSlash(resolveWsBase())
  const normalizedPath = path ? `/${path.toString().replace(/^\/+/, '')}` : ''
  let search = ''
  if (query && typeof query === 'object') {
    const params = new URLSearchParams()
    Object.entries(query).forEach(([key, value]) => {
      if (value === undefined || value === null) return
      params.append(key, String(value))
    })
    const qs = params.toString()
    if (qs) {
      search = `?${qs}`
    }
  }
  return `${base}${normalizedPath}${search}`
}
