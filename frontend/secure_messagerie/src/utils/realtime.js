// ===== Realtime Helpers =====
// Construit les URLs WebSocket a partir de la config (ou du navigateur) pour garantir des connexions temps reel coherentes.

// ---- Constantes ----
// Origine HTTP utilisee quand l'app tourne hors navigateur (tests, prerender).
const DEFAULT_HTTP_ORIGIN = 'http://localhost:8000'

// ---- Utils de normalisation ----
// Supprime les slashs finaux pour eviter les doubles slashs lors des concatenations.
function stripTrailingSlash(value) {
  return value.replace(/\/+$/, '')
}

// Retourne l'origine courante (browser) ou un defaut connu pour reconstruire les URLs.
function getRuntimeOrigin() {
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin
  }
  return DEFAULT_HTTP_ORIGIN
}

// S'assure que la base API se termine par "/api" pour simplifier la suite des calculs.
function normalizeApiBase(candidate) {
  const raw = (candidate || '').toString().trim()
  if (!raw) return '/api'
  const trimmed = stripTrailingSlash(raw)
  return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`
}

let cachedWsBase = ''

// ---- Resolution de l'URL WS ----
// Utilise VITE_WS_BASE si present, sinon derive la base depuis VITE_API_URL + origine courante, avec fallback robuste.
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

// ---- Construction finale ----
// Assemble la base WS avec un chemin et des query params optionnels deja filtres pour ignorer les valeurs nulles.
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
