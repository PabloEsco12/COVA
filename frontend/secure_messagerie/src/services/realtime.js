// src/services/realtime.js
import { backendBase } from '@/utils/api'

function buildWsUrl(path) {
  const base = backendBase.replace(/\/+$/, '')
  // Important: utiliser l'URL relative pour éviter les doubles /api
  const url = new URL(`/api${path}`, base)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return url
}

/**
 * WebSocket conversation avec:
 * - auto-reconnexion exponentielle (jusqu'à 20s)
 * - heartbeat (ping toutes 30s, timeout 15s)
 * - API identique à ta version: createConversationSocket(convId, { token, onEvent, onOpen, onError, onClose })
 *
 * Retourne un objet compatible WebSocket pour .close() et expose .send(data) en plus.
 */
export function createConversationSocket(
  conversationId,
  { token, onEvent, onOpen, onError, onClose } = {}
) {
  const url = buildWsUrl(`/ws/conversations/${conversationId}`)
  if (token) url.searchParams.set('token', token)

  let socket = null
  let closedManually = false

  // Reco
  let retry = 0
  const minDelay = 800
  const maxDelay = 20000

  // Heartbeat
  let heartbeatTimer = null
  let heartbeatTimeout = null
  const HEARTBEAT_INTERVAL = 30000 // 30s
  const HEARTBEAT_DEADLINE = 15000 // 15s

  function clearHeartbeat() {
    if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
    if (heartbeatTimeout) { clearTimeout(heartbeatTimeout); heartbeatTimeout = null }
  }

  function startHeartbeat() {
    clearHeartbeat()
    heartbeatTimer = setInterval(() => {
      // si le socket n’est pas prêt on ne ping pas
      if (!socket || socket.readyState !== WebSocket.OPEN) return
      try { socket.send(JSON.stringify({ event: 'ping' })) } catch (_) {}
      // si pas de réponse dans la deadline → on force la reconnexion
      heartbeatTimeout = setTimeout(() => {
        try { socket.close() } catch (_) {}
      }, HEARTBEAT_DEADLINE)
    }, HEARTBEAT_INTERVAL)
  }

  function handleMessage(evt) {
    // On considère toute activité comme un “pong” implicite
    if (heartbeatTimeout) { clearTimeout(heartbeatTimeout); heartbeatTimeout = null }

    if (!onEvent) return
    try {
      const payload = JSON.parse(evt.data)
      onEvent(payload, evt)
    } catch (err) {
      console.warn('Unable to parse realtime payload', err)
    }
  }

  function connect() {
    // sécurité: si fermeture manuelle, on ne relance pas
    if (closedManually) return

    socket = new WebSocket(url.toString())

    socket.addEventListener('open', () => {
      retry = 0
      startHeartbeat()
      onOpen && onOpen()
    })

    socket.addEventListener('message', handleMessage)

    socket.addEventListener('error', (e) => {
      onError && onError(e)
      // l’erreur se gère via close pour reco
    })

    socket.addEventListener('close', () => {
      clearHeartbeat()
      onClose && onClose()
      if (closedManually) return
      // backoff exponentiel
      const delay = Math.min(maxDelay, Math.floor(minDelay * Math.pow(2, retry++)))
      setTimeout(connect, delay)
    })
  }

  connect()

  // Interface renvoyée
  return {
    // Expose un send sécurisé
    send(data) {
      try {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(typeof data === 'string' ? data : JSON.stringify(data))
        }
      } catch (_) {}
    },
    // Ferme proprement et coupe la reco
    close(code, reason) {
      closedManually = true
      clearHeartbeat()
      try { socket && socket.close(code, reason) } catch (_) {}
    },
    // Compat “vieux” code qui attend l’instance WebSocket (rarement utile)
    get raw() {
      return socket
    },
  }
}
