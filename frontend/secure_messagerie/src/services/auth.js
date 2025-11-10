import { api } from '@/utils/api'

const SESSION_STORAGE_KEY = 'securechat.session'

function persistLegacyKeys(session) {
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
    // Backward compatibility for components still expecting pseudo
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
  try {
    localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session))
    persistLegacyKeys(session)
  } catch (err) {
    console.warn('Unable to persist session payload', err)
  }
  return session
}

export function loadSession() {
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
}

export async function registerAccount({ email, password, displayName }) {
  const payload = {
    email,
    password,
    display_name: displayName || null,
  }
  const { data } = await api.post('/auth/register', payload)
  return data
}

export async function loginWithPassword({ email, password, totpCode }) {
  const { data } = await api.post('/auth/login', {
    email,
    password,
    totp_code: totpCode || undefined,
  })
  return persistSession(data)
}

export async function refreshSession(refreshToken) {
  const token = refreshToken ?? localStorage.getItem('refresh_token')
  if (!token) {
    throw new Error('No refresh token available')
  }
  const { data } = await api.post('/auth/refresh', { refresh_token: token })
  return persistSession(data)
}

export async function logout(refreshToken) {
  const token = refreshToken ?? localStorage.getItem('refresh_token')
  if (!token) return
  await api.post('/auth/logout', { refresh_token: token })
  clearSession()
}

export async function resendConfirmationEmail(email) {
  await api.post('/auth/resend-confirmation', { email })
}

export async function logoutAll() {
  await api.post('/auth/logout-all')
  clearSession()
}

export function getCurrentUserFromCache() {
  const session = loadSession()
  return session?.user ?? null
}

export function getAccessToken() {
  try {
    return localStorage.getItem('access_token')
  } catch {
    return null
  }
}
