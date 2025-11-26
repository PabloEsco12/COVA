// ===== Profile Utilities =====
// Fonctions partagees pour deriver les initiales, normaliser l'URL d'avatar et propager les mises a jour de profil.

// ---- Initiales d'avatar ----
// Genere deux caracteres lisibles a partir du displayName ou de l'email pour les avatars par defaut.
export function computeAvatarInitials(options = {}) {
  const { displayName = '', email = '', fallback = 'SC' } = options || {}
  const base = (displayName || '').trim() || (email || '').trim()
  if (!base) {
    return fallback
  }
  const parts = base
    .replace(/[_\-@.]+/g, ' ')
    .split(/\s+/)
    .filter(Boolean)
  const [first = '', second = ''] = parts
  const initials = `${first.charAt(0)}${second.charAt(0)}`.trim()
  if (initials) {
    return initials.toUpperCase()
  }
  if (first) {
    return first.slice(0, 2).toUpperCase()
  }
  return (base.charAt(0) || fallback).toUpperCase()
}

// ---- Normalisation d'URL ----
// Convertit une valeur d'avatar en URL exploitable : prefixe avec baseUrl si necessaire et ajoute un cache-bust optionnel.
export function normalizeAvatarUrl(url, { baseUrl = '', cacheBust = false } = {}) {
  if (!url) {
    return null
  }
  let normalized = url.trim()
  const hasScheme = /^https?:\/\//i.test(normalized)
  if (baseUrl) {
    const base = baseUrl.replace(/\/$/, '')
    if (!hasScheme) {
      const path = normalized.startsWith('/') ? normalized : `/${normalized}`
      normalized = `${base}${path}`
    } else {
      try {
        const absolute = new URL(normalized)
        const targetBase = new URL(base)
        if (absolute.origin !== targetBase.origin) {
          const path = absolute.pathname + absolute.search
          normalized = `${base}${path}`
        }
      } catch {
        // if URL parsing fails, fallback to prefixing base
        const path = normalized.startsWith('/') ? normalized : `/${normalized.replace(/^https?:\/\//i, '')}`
        normalized = `${base}${path}`
      }
    }
  }
  if (cacheBust) {
    const separator = normalized.includes('?') ? '&' : '?'
    normalized = `${normalized}${separator}v=${Date.now()}`
  }
  return normalized
}

// ---- Broadcast des changements ----
// Met a jour le localStorage et emet un CustomEvent pour que l'UI reagisse immediatement aux modifications de profil.
export function broadcastProfileUpdate(payload = {}) {
  const detail = {}
  if (Object.prototype.hasOwnProperty.call(payload, 'display_name')) {
    detail.display_name = payload.display_name
    try {
      if (payload.display_name) {
        localStorage.setItem('pseudo', payload.display_name)
      } else {
        localStorage.removeItem('pseudo')
      }
    } catch {}
  }
  if (Object.prototype.hasOwnProperty.call(payload, 'avatar_url')) {
    detail.avatar_url = payload.avatar_url || null
    try {
      if (payload.avatar_url) {
        localStorage.setItem('avatar_url', payload.avatar_url)
      } else {
        localStorage.removeItem('avatar_url')
      }
    } catch {}
  }
  if (Object.prototype.hasOwnProperty.call(payload, 'email')) {
    detail.email = payload.email
  }
  if (Object.prototype.hasOwnProperty.call(payload, 'status_message')) {
    detail.status_message = payload.status_message || ''
    try {
      if (payload.status_message) {
        localStorage.setItem('status_message', payload.status_message)
      } else {
        localStorage.removeItem('status_message')
      }
    } catch {}
  }
  if (Object.prototype.hasOwnProperty.call(payload, 'status_code')) {
    detail.status_code = payload.status_code || ''
    try {
      if (payload.status_code) {
        localStorage.setItem('status_code', payload.status_code)
      } else {
        localStorage.removeItem('status_code')
      }
    } catch {}
  }
  if (typeof window !== 'undefined') {
    try {
      window.dispatchEvent(new CustomEvent('cova:profile-update', { detail }))
    } catch {
      /* noop */
    }
  }
}
