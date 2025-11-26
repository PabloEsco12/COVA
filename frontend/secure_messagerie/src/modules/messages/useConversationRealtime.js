// ===== Module Header =====
// Module: messages/useConversationRealtime
// Role: Ouvre le socket conversation + flux notifications; route les evenements (messages, typing, presence, appels).
// Notes:
//  - Exige un token (authToken) et des callbacks injectes pour appliquer les payloads.
//  - Fournit sendCallSignal/setCallEventHandler pour brancher la logique WebRTC du module appel.

import { ref, watch } from 'vue'
import { useNotificationsStream } from '@/composables/useNotificationsStream'
import { createConversationSocket } from '@/services/realtime'

export function useConversationRealtime({
  selectedConversationId,
  currentUserId,
  normalizeMessage,
  ensureMeta,
  pagination,
  applyMessageUpdate,
  markConversationAsRead,
  incrementUnreadCounter,
  notifyNewIncomingMessage,
  handleRealtimeTyping,
  applyPresencePayload,
  resetPresenceState,
  processNotificationPayload,
  isConversationMuted,
}) {
  const authToken = ref(localStorage.getItem('access_token') || null)
  const socketRef = ref(null)
  const connectionStatus = ref('idle')
  const realtimeConversationId = ref(null)
  const callEventHandler = ref(null)
  const stopTypingHandler = ref(() => {})

  const notificationsStream = useNotificationsStream({
    token: authToken.value,
    onNotification: (payload) => processNotificationPayload(payload, 'stream'),
  })

  const callLog = (...args) => {
    try {
      console.info('[call]', ...args)
    } catch {}
  }

  // ---- Emission de signaux d'appel (offer/answer/candidate/hangup) vers le socket ----
  function sendCallSignal(event, payload = {}) {
    if (!socketRef.value || !selectedConversationId.value) return
    try {
      callLog('send signal', event, payload.call_id || null, payload.reason || '')
      socketRef.value.send({
        event,
        payload: {
          conversation_id: selectedConversationId.value,
          ...payload,
        },
      })
    } catch {}
  }

  function setCallEventHandler(handler) {
    callEventHandler.value = typeof handler === 'function' ? handler : null
  }

  function setStopLocalTyping(handler) {
    if (typeof handler === 'function') {
      stopTypingHandler.value = handler
    }
  }

  // ---- Traitement des messages recues via websocket (message, presence, typing) ----
  function handleIncomingRealtime(payload) {
    const type = typeof payload?.event === 'string' ? payload.event : 'message'
    const message = normalizeMessage(payload, { selfId: currentUserId.value })
    const meta = ensureMeta(message.conversationId)

    if (typeof message.streamPosition === 'number') {
      pagination.afterCursor = pagination.afterCursor
        ? Math.max(pagination.afterCursor, message.streamPosition)
        : message.streamPosition
    }

    if (type === 'message') {
      meta.lastPreview = message.preview
      meta.lastActivity = message.createdAt
    }

    const isSameConversation = message.conversationId === selectedConversationId.value
    const shouldProcess = type === 'message' && !message.sentByMe && !message.isSystem && !message.deleted
    const isMuted = typeof isConversationMuted === 'function' && isConversationMuted(message.conversationId)
    const allowAlert = shouldProcess && !isMuted

    if (isSameConversation) {
      applyMessageUpdate(message)
      if (shouldProcess) {
        markConversationAsRead(message.conversationId, [message.id]).catch(() => {})
      }
    } else if (shouldProcess) {
      incrementUnreadCounter(message.conversationId)
    }

    if (
      allowAlert &&
      (!isSameConversation || (typeof document !== 'undefined' && (document.hidden || !document.hasFocus())))
    ) {
      if (typeof notifyNewIncomingMessage === 'function') {
        notifyNewIncomingMessage(message)
      }
    }
  }

  // ---- Ferme proprement le socket (option preserve presence/conversation) ----
  function disconnectRealtime(options = {}) {
    const { preserveConversation = false, preservePresence = false } = options
    if (socketRef.value) {
      try {
        socketRef.value.close()
      } catch {}
      socketRef.value = null
    }
    connectionStatus.value = 'idle'
    stopTypingHandler.value()
    if (!preservePresence && typeof resetPresenceState === 'function') {
      resetPresenceState()
    }
    if (!preserveConversation) {
      realtimeConversationId.value = null
    }
  }

  // ---- Ouvre le socket conversation et route les evenements ----
  function connectRealtime(convId, options = {}) {
    const targetId = convId ? String(convId) : null
    if (!targetId || !authToken.value) {
      disconnectRealtime(options)
      return
    }

    const { force = false, preservePresence = false } = options
    const sameConversation = realtimeConversationId.value === targetId
    if (!force && sameConversation && socketRef.value) {
      return
    }

    if (socketRef.value) {
      disconnectRealtime({
        preserveConversation: sameConversation,
        preservePresence: preservePresence && sameConversation,
      })
    }

    connectionStatus.value = 'connecting'
    realtimeConversationId.value = targetId
    socketRef.value = createConversationSocket(targetId, {
      token: authToken.value,
      onOpen: () => {
        connectionStatus.value = 'connected'
      },
      onError: () => {
        connectionStatus.value = 'error'
      },
      onClose: () => {
        connectionStatus.value = 'idle'
      },
      onEvent: (payload) => {
        if (!payload || typeof payload !== 'object') return
        switch (payload.event) {
          case 'ready':
            connectionStatus.value = 'connected'
            return
          case 'message':
          case 'message.updated':
            handleIncomingRealtime(payload)
            return
          case 'typing:start':
          case 'typing:stop':
            handleRealtimeTyping(payload)
            return
          case 'presence:update':
            applyPresencePayload(payload.payload)
            return
          case 'call:offer':
          case 'call:answer':
          case 'call:candidate':
          case 'call:hangup':
            callEventHandler.value?.(payload)
            return
          default:
            break
        }
      },
    })
  }

  watch(authToken, (token) => {
    notificationsStream.updateToken(token || null)
    if (!token) {
      disconnectRealtime()
      return
    }
    if (selectedConversationId.value) {
      connectRealtime(selectedConversationId.value, { force: true, preservePresence: true })
    }
  })

  return {
    authToken,
    socketRef,
    connectionStatus,
    realtimeConversationId,
    notificationsStream,
    sendCallSignal,
    connectRealtime,
    disconnectRealtime,
    handleIncomingRealtime,
    setCallEventHandler,
    setStopLocalTyping,
  }
}
