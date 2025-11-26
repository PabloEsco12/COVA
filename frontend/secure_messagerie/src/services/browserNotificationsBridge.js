// Bridge WebSocket pour convertir les evenements serveur en notifications navigateur
import { buildWsUrl } from '@/utils/realtime'

const PREF_KEY = 'notif_browser'

// --- Gestion des notifications push cote navigateur ---
class BrowserNotificationsBridge {
  constructor() {
    // Installe les ecouteurs pour suivre token/prefs, puis ouvre un WS si possible
    if (typeof window === 'undefined') return
    this.socket = null
    this.reconnectTimer = null
    this.backoff = 0
    this.token = this.readToken()
    this.enabled = this.readPreference()
    window.__covaGlobalBrowserNotifications = true
    this.handleStorage = this.handleStorage.bind(this)
    this.handlePrefBroadcast = this.handlePrefBroadcast.bind(this)
    this.handleSessionUpdate = this.handleSessionUpdate.bind(this)
    this.handleSessionClear = this.handleSessionClear.bind(this)
    window.addEventListener('storage', this.handleStorage)
    window.addEventListener('cova:browser-notifications', this.handlePrefBroadcast)
    window.addEventListener('cova:session-update', this.handleSessionUpdate)
    window.addEventListener('cova:session-clear', this.handleSessionClear)
    if (this.token) {
      this.connect()
    }
  }

  readToken() {
    // Recupere le token d'acces stocke par le service auth
    try {
      return localStorage.getItem('access_token')
    } catch {
      return null
    }
  }

  readPreference() {
    // Preference utilisateur (1/0) pour activer la notification navigateur
    try {
      return localStorage.getItem(PREF_KEY) === '1'
    } catch {
      return false
    }
  }

  handleStorage(event) {
    // Synchronise les changements provenant d'autres onglets (token ou preference)
    if (event.key === 'access_token') {
      this.handleSessionUpdate({ detail: { token: event.newValue || null } })
    } else if (event.key === PREF_KEY) {
      this.enabled = event.newValue === '1'
    }
  }

  handlePrefBroadcast(event) {
    // Reception d'un CustomEvent interne pour aligner la preference entre composants
    if (event?.detail && typeof event.detail.enabled === 'boolean') {
      this.enabled = event.detail.enabled
    }
  }

  handleSessionUpdate(event) {
    // Ouvre ou reouvre le WS lorsqu'un token change
    const nextToken = event?.detail?.token || this.readToken()
    if (nextToken === this.token) return
    this.token = nextToken
    this.connect(true)
  }

  handleSessionClear() {
    // Nettoie la connexion des que la session est supprimee
    this.token = null
    this.disposeSocket()
  }

  scheduleReconnect() {
    // Backoff exponentiel (limite a 20s) pour retenter une connexion stable
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }
    if (!this.token) return
    const baseDelay = 1500
    const delay = Math.min(20000, baseDelay * Math.pow(2, this.backoff))
    this.backoff = Math.min(this.backoff + 1, 8)
    this.reconnectTimer = setTimeout(() => this.connect(true), delay)
  }

  disposeSocket() {
    // Ferme proprement la socket et annule les timers associes
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.socket) {
      try {
        this.socket.close()
      } catch {
        // ignore
      }
      this.socket = null
    }
  }

  connect(force = false) {
    // Etablit la connexion WS vers le pont notifications (ou force le refresh)
    if (!this.token) {
      this.disposeSocket()
      return
    }
    if (this.socket && !force) {
      return
    }
    this.disposeSocket()
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    const url = new URL(buildWsUrl('notifications', { token: this.token }))
    const ws = new WebSocket(url)
    ws.onopen = () => {
      this.backoff = 0
    }
    ws.onerror = () => {
      ws.close()
    }
    ws.onclose = () => {
      this.scheduleReconnect()
    }
    ws.onmessage = (event) => {
      this.handleMessage(event)
    }
    this.socket = ws
  }

  handleMessage(event) {
    // Parse les evenements WS et redispatche un CustomEvent exploitable par l'UI
    if (!event?.data) return
    let data
    try {
      data = JSON.parse(event.data)
    } catch {
      return
    }
    if (data.event !== 'notification') return
    const payload = { ...(data.payload || {}), __origin: 'bridge' }
    window.dispatchEvent(new CustomEvent('cova:notification-event', { detail: payload }))
    this.maybeTriggerBrowserNotification(payload)
  }

  maybeTriggerBrowserNotification(payload) {
    // Affiche une notification native si l'utilisateur l'a autorisee
    if (!this.enabled) return
    if (typeof Notification === 'undefined') return
    if (Notification.permission !== 'granted') return
    const meta = this.normalizePayload(payload)
    const notification = new Notification(meta.title, {
      body: meta.body,
      tag: meta.tag,
    })
    notification.onclick = () => {
      try {
        window.focus()
      } catch {
        // ignore
      }
      if (meta.conversationId) {
        const detail = { id: meta.conversationId, messageId: meta.messageId }
        window.dispatchEvent(new CustomEvent('cova:open-conversation', { detail }))
        if (!window.location.pathname?.startsWith('/dashboard/messages')) {
          const search = new URLSearchParams({ conversation: meta.conversationId })
          window.location.href = `/dashboard/messages?${search.toString()}`
        }
      }
      notification.close()
    }
    setTimeout(() => notification.close(), 8000)
  }

  normalizePayload(payload) {
    // Uniformise les attributs attendus par la notification native selon le type d'evenement
    if (payload?.type === 'message.received') {
      return {
        title: payload.sender || 'Nouveau message',
        body: payload.preview || 'Message sécurisé',
        tag: payload.conversation_id || 'message',
        conversationId: payload.conversation_id || null,
        messageId: payload.message_id || null,
      }
    }
    return {
      title: payload?.title || 'Notification',
      body: payload?.body || '',
      tag: payload?.type || 'notification',
      conversationId: payload?.conversation_id || null,
      messageId: payload?.message_id || null,
    }
  }
}

export const browserNotificationsBridge =
  typeof window !== 'undefined' ? new BrowserNotificationsBridge() : null
