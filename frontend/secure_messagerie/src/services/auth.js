// Service d'authentification : persistance locale, diffusion d'evenements et appels API
import { api } from '@/utils/api'
import { broadcastProfileUpdate } from '@/utils/profile'

const SESSION_STORAGE_KEY = 'securechat.session'

// --- Evénements et persistance de session ---
function emitSessionEvent(name, detail = {}) {
  // Simplifie la diffusion d'un changement de session via CustomEvent
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(name, { detail }))
}

function persistLegacyKeys(session) {
  // Repousse les champs attendus par d'anciens composants (compatibilite ascendante)
  try {
    const { tokens, user } = session
    if (tokens?.access_token) {
      localStorage.setItem('access_token', tokens.access_token)
    }
    if (tokens?.refresh_token) {
      localStorage.setItem('refresh_token', tokens.refresh_token)
    }
    if (user?.id) {
      localStorage.setItem('user_id', String(user.id))
    }
    if (user?.email) {
      localStorage.setItem('user_email', user.email)
    }
    const displayName = user?.profile?.display_name ?? ''
    if (displayName) {
      localStorage.setItem('user_display_name', displayName)
    } else {
      localStorage.removeItem('user_display_name')
    }
    // Rétrocompatibilité pour les composants qui attendent encore pseudo
    if (displayName) {
      localStorage.setItem('pseudo', displayName)
    } else {
      localStorage.removeItem('pseudo')
    }
  } catch (err) {
    console.warn('Unable to persist legacy auth keys', err)
  }
}

export function persistSession(session) {
  // Stocke la session courante et notifie l'application du changement de token
  try {
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session))
    persistLegacyKeys(session)
  } catch (err) {
    console.warn('Unable to persist session payload', err)
  }
  const token = session?.tokens?.access_token || null
  emitSessionEvent('cova:session-update', { token })
  return session
}

export function loadSession() {
  // Charge la session brute depuis le storage (ou null en cas d'absence/erreur)
  try {
    const raw = localStorage.getItem(SESSION_STORAGE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch (err) {
    console.warn('Unable to load cached session', err)
    return null
  }
}

export function clearSession() {
  // Purge totale des traces de session et notification globale
  try {
    localStorage.removeItem(SESSION_STORAGE_KEY)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_id')
    localStorage.removeItem('user_email')
    localStorage.removeItem('user_display_name')
    localStorage.removeItem('avatar_url')
    localStorage.removeItem('pseudo')
  } catch (err) {
    console.warn('Unable to clear session storage', err)
  }
  emitSessionEvent('cova:session-clear')
}

// --- Flux d'authentification ---
export async function registerAccount({ email, password, displayName }) {
  // Cree un compte et renvoie le payload de session (tokens + user)
  const payload = {
    email,
    password,
    display_name: displayName || null,
  }
  const { data } = await api.post('/auth/register', payload)
  return data
}

export async function loginWithPassword({ email, password, totpCode }) {
  // Login classique + support TOTP; persiste la session obtenue
  const timezone =
    typeof Intl !== 'undefined' && Intl.DateTimeFormat ? Intl.DateTimeFormat().resolvedOptions().timeZone : null
  const { data } = await api.post('/auth/login', {
    email,
    password,
    totp_code: totpCode || undefined,
    timezone: timezone || undefined,
  })
  return persistSession(data)
}

export async function refreshSession(refreshToken) {
  // Rafraichit le token d'acces a partir du refresh token fourni ou stocke
  const token = refreshToken ?? localStorage.getItem('refresh_token')
  if (!token) {
    throw new Error('No refresh token available')
  }
  const { data } = await api.post('/auth/refresh', { refresh_token: token })
  return persistSession(data)
}

export async function logout(refreshToken) {
  // Deconnexion serveur + reset presence, toujours suivi d'un nettoyage local
  const token = refreshToken ?? localStorage.getItem('refresh_token')
  try {
    if (token) {
      await api.post('/auth/logout', { refresh_token: token })
    }
    await setPresenceStatus('Hors ligne', 'offline')
  } finally {
    clearSession()
  }
}

export async function resendConfirmationEmail(email) {
  // Renvoie l'email de confirmation pour un compte non valide
  await api.post('/auth/resend-confirmation', { email })
}

export async function logoutAll() {
  // Deconnexion de tous les devices puis remise a zero de la session locale
  try {
    await api.post('/auth/logout-all')
    await setPresenceStatus('Hors ligne', 'offline')
  } finally {
    clearSession()
  }
}

// --- Acces aux infos de session ---
export function getCurrentUserFromCache() {
  // Retourne l'utilisateur memorise sans requete reseau
  const session = loadSession()
  return session?.user ?? null
}

export function getAccessToken() {
  // Lecture securisee du token d'acces (evite crash en mode SSR)
  try {
    return localStorage.getItem('access_token')
  } catch {
    return null
  }
}

// --- Verification et expiration de token ---
function decodeJwtPayload(token) {
  // Decode la charge utile du JWT pour extraire exp/claims sans verifier la signature
  if (!token) return null
  try {
    const [, payload = ''] = token.split('.')
    if (!payload) return null
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const padded = normalized.padEnd(normalized.length + (4 - (normalized.length % 4)) % 4, '=')
    const decoded = atob(padded)
    return JSON.parse(decoded)
  } catch {
    return null
  }
}

export function isAccessTokenExpired(token = null) {
  const value = token || getAccessToken()
  if (!value) return true
  const payload = decodeJwtPayload(value)
  if (!payload?.exp) return false
  const now = Math.floor(Date.now() / 1000)
  // Petite marge de sécurité de 30s
  // Ajout d'une marge pour couvrir d'eventuels delais reseau ou decalages d'horloge
  return payload.exp <= now - 30
}

export function hasStoredSession() {
  // Indique si des artefacts de session sont presentes pour conditionner le bootstrap
  try {
    return Boolean(
      localStorage.getItem(SESSION_STORAGE_KEY) ||
        localStorage.getItem('access_token') ||
        localStorage.getItem('refresh_token'),
    )
  } catch {
    return false
  }
}

// --- Presence / statut utilisateur ---
export async function setPresenceStatus(message, statusCode) {
  // Met a jour le statut distant puis diffuse localement pour synchroniser l'UI
  try {
    await api.put('/me/profile', { status_message: message || null })
    broadcastProfileUpdate({
      status_message: message || '',
      status_code: statusCode || '',
    })
  } catch (err) {
    console.warn('Unable to update presence status', err)
  }
}
