// ===== Composable Header =====
// Composable: useRealtime
// Author: Valentin Masurelle
// Date: 2025-11-26
// Role: WebSocket temps réel (messages, typing, présence) avec reconnect/backoff/heartbeat.
// Usage:
//  - Créer avec l'ID de conversation et des handlers (onMessageNew/onTyping/etc.).
//  - send/sendTypingStart/sendTypingStop pour émettre des événements.
//  - updateConversation reconnecte proprement sur une nouvelle conversation.
//  - Heartbeat périodique pour garder la socket active derrière les proxys.
// src/composables/useRealtime.js
import { ref, onBeforeUnmount, onMounted, watch } from 'vue'
import { buildWsUrl } from '@/utils/realtime'

/**
 * WebSocket avec auto-reconnexion (exponential backoff), heartbeat et handlers d'événements.
 *
 * Événements attendus côté backend:
 *  - message:new        { id, ... }
 *  - message:update     { id, ... }
 *  - message:delete     { id }
 *  - typing:start/stop  { user_id, ... }
 *  - presence:update    { users: [...] }
 *
 * Options d’URL:
 *  - VITE_WS_BASE = wss://api.cova.be/ws   (ou ws://localhost:8000/ws)
 *
 * @param {string|number|null} initialConversationId
 * @param {Object} handlers
 * @param {Function} [handlers.onMessageNew]
 * @param {Function} [handlers.onMessageUpdate]
 * @param {Function} [handlers.onMessageDelete]
 * @param {Function} [handlers.onTyping]
 * @param {Function} [handlers.onPresence]
 */
export function useRealtime(initialConversationId, handlers = {}) {
  const socket = ref(null)
  const connected = ref(false)
  const conversationId = ref(initialConversationId ?? null)

  // timers
  const reconnectTimer = ref(null)
  const heartbeatTimer = ref(null)

  // backoff
  const baseDelay = 1500
  const maxDelay = 30000
  const backoffStep = ref(0)

  function makeUrl() {
    if (!conversationId.value) return null
    const token = localStorage.getItem('access_token') || ''
    if (!token) return null
    return buildWsUrl(`conversations/${conversationId.value}`, { token })
  }

  function scheduleReconnect() {
    clearReconnect()
    const delay = Math.min(maxDelay, baseDelay * Math.pow(2, backoffStep.value))
    reconnectTimer.value = setTimeout(connect, delay)
    backoffStep.value = Math.min(backoffStep.value + 1, 10)
  }

  function clearReconnect() {
    if (reconnectTimer.value) {
      clearTimeout(reconnectTimer.value)
      reconnectTimer.value = null
    }
  }

  function startHeartbeat() {
    stopHeartbeat()
    // Envoie un ping périodique pour garder la socket vivante côté proxy/WS
    heartbeatTimer.value = setInterval(() => {
      safeSend({ event: 'ping', payload: { ts: Date.now() } })
    }, 25000)
  }

  function stopHeartbeat() {
    if (heartbeatTimer.value) {
      clearInterval(heartbeatTimer.value)
      heartbeatTimer.value = null
    }
  }

  function connect() {
    const url = makeUrl()
    if (!url) {
      disconnect()
      return
    }

    // Nettoie au cas où
    disconnect(false)

    const ws = new WebSocket(url)
    socket.value = ws

    ws.onopen = () => {
      connected.value = true
      // reset backoff au 1er succès
      backoffStep.value = 0

      // S’abonner explicitement (selon ton backend)
      safeSend({ event: 'subscribe', payload: { conversation_id: conversationId.value } })

      // Heartbeat
      startHeartbeat()
    }

    ws.onclose = () => {
      connected.value = false
      stopHeartbeat()
      scheduleReconnect()
    }

    ws.onerror = (err) => {
      // Erreur réseau/transitoire => on laisse onclose gérer la reconnexion
      // (les proxys ferment souvent la socket juste après l’erreur)
      // On log quand même en dev.
      if (import.meta.env.DEV) {
        console.warn('[Realtime] erreur socket', err)
      }
    }

    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data)
        const type = data?.event
        switch (type) {
          case 'message:new':
            handlers.onMessageNew?.(data.payload)
            break
          case 'message:update':
            handlers.onMessageUpdate?.(data.payload)
            break
          case 'message:delete':
            handlers.onMessageDelete?.(data.payload)
            break
          case 'typing:start':
          case 'typing:stop':
            handlers.onTyping?.(data)
            break
          case 'presence:update':
            handlers.onPresence?.(data.payload)
            break
          case 'pong': // si ton backend répond au ping
            // no-op
            break
          default:
            // silencieux
            break
        }
      } catch (e) {
        console.error('[Realtime] parse error', e)
      }
    }
  }

  function safeSend(obj) {
    if (!socket.value || socket.value.readyState !== WebSocket.OPEN) return
    try {
      socket.value.send(JSON.stringify(obj))
    } catch {
      // ignore
    }
  }

  function send(event, payload = {}) {
    safeSend({ event, payload })
  }

  function sendTypingStart() {
    send('typing:start', { conversation_id: conversationId.value })
  }

  function sendTypingStop() {
    send('typing:stop', { conversation_id: conversationId.value })
  }

  /**
   * Déconnecte la socket.
   * @param {boolean} [clearRetry=true] - si true, annule aussi la reconnexion programmée
   */
  function disconnect(clearRetry = true) {
    stopHeartbeat()
    if (clearRetry) clearReconnect()
    if (socket.value) {
      try { socket.value.close() } catch {}
      socket.value = null
    }
    connected.value = false
  }

  /**
   * Met à jour la conversation cible et reconnecte automatiquement.
   * @param {string|number|null} newId
   */
  function updateConversation(newId) {
    const next = newId ?? null
    if (conversationId.value === next) return
    conversationId.value = next
    if (!next) {
      disconnect()
      return
    }
    // on force une nouvelle connexion propre
    connect()
  }

  // Reconnecte si le token JWT change (ex: nouvelle connexion)
  const tokenKey = 'access_token'
  const originalSetItem = localStorage.setItem
  localStorage.setItem = function patchedSetItem(key, value) {
    originalSetItem.apply(this, arguments)
    if (key === tokenKey && conversationId.value) {
      // Token mis à jour => reconnecter pour prendre en compte le nouveau JWT
      connect()
    }
  }

  // Pause le heartbeat si onglet caché (quelques proxys tuent les WS inactifs)
  function handleVisibility() {
    if (document.hidden) {
      stopHeartbeat()
    } else if (connected.value) {
      startHeartbeat()
    }
  }

  onMounted(() => {
    document.addEventListener('visibilitychange', handleVisibility)
    if (conversationId.value) connect()
  })

  onBeforeUnmount(() => {
    document.removeEventListener('visibilitychange', handleVisibility)
    // remet le setItem d’origine pour ne pas “polluer” le runtime global
    localStorage.setItem = originalSetItem
    disconnect()
  })

  // Si la conversation passée à la création du composable est réactive dans ton composant parent,
  // tu peux aussi watcher ici (optionnel, sinon utilise updateConversation depuis ton composant).
  watch(conversationId, (val, oldVal) => {
    if (val !== oldVal && val) {
      connect()
    }
  })

  return {
    // état
    connected,

    // contrôle
    connect,
    disconnect,

    // conversation dynamique
    updateConversation,

    // envoi custom
    send,
    sendTypingStart,
    sendTypingStop,
  }
}
