// src/services/realtime.js
import { buildWsUrl } from '@/utils/realtime'

/**
 * WebSocket conversation avec:
 * - auto-reconnexion exponentielle (jusqu'à 20s)
 * - heartbeat (ping toutes 30s, timeout 15s)
 * - API identique à la version historique : createConversationSocket(convId, { token, onEvent, onOpen, onError, onClose })
 *
 * Retourne un objet compatible WebSocket pour .close() et expose .send(data) en plus.
 */
export function createConversationSocket(conversationId, { token, onEvent, onOpen, onError, onClose } = {}) {
  const url = new URL(buildWsUrl(`conversations/${conversationId}`, token ? { token } : undefined))

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
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
    if (heartbeatTimeout) {
      clearTimeout(heartbeatTimeout)
      heartbeatTimeout = null
    }
  }

  function startHeartbeat() {
    clearHeartbeat()
    heartbeatTimer = setInterval(() => {
      if (!socket || socket.readyState !== WebSocket.OPEN) return
      try {
        socket.send(JSON.stringify({ event: 'ping' }))
      } catch {
        // silencieux
      }
      heartbeatTimeout = setTimeout(() => {
        try {
          socket.close()
        } catch {
          // silencieux
        }
      }, HEARTBEAT_DEADLINE)
    }, HEARTBEAT_INTERVAL)
  }

  function handleMessage(evt) {
    if (heartbeatTimeout) {
      clearTimeout(heartbeatTimeout)
      heartbeatTimeout = null
    }

    if (!onEvent) return
    try {
      const payload = JSON.parse(evt.data)
      onEvent(payload, evt)
    } catch (err) {
      console.warn('Unable to parse realtime payload', err)
    }
  }

  function connect() {
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
    })

    socket.addEventListener('close', () => {
      clearHeartbeat()
      onClose && onClose()
      if (closedManually) return
      const delay = Math.min(maxDelay, Math.floor(minDelay * Math.pow(2, retry++)))
      setTimeout(connect, delay)
    })
  }

  connect()

  return {
    send(data) {
      try {
        if (socket && socket.readyState === WebSocket.OPEN) {
          socket.send(typeof data === 'string' ? data : JSON.stringify(data))
        }
      } catch {
        // silencieux
      }
    },
    close(code, reason) {
      closedManually = true
      clearHeartbeat()
      try {
        socket && socket.close(code, reason)
      } catch {
        // silencieux
      }
    },
    get raw() {
      return socket
    },
  }
}
