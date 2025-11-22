import { ref } from 'vue'
import { createConversationSocket } from '@/services/realtime'

export function useRealtimeMessaging({
  authToken,
  normalizeMessage,
  ensureMeta,
  pagination,
  selectedConversationId,
  applyMessageUpdate,
  markConversationAsRead,
  incrementUnreadCounter,
  notifyNewIncomingMessage,
}) {
  const socketRef = ref(null)
  const connectionStatus = ref('idle')

  function handleIncomingRealtime(payload) {
    const type = typeof payload?.event === 'string' ? payload.event : 'message'
    const message = normalizeMessage(payload)
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
    const shouldNotify = type === 'message' && !message.sentByMe && !message.isSystem && !message.deleted

    if (isSameConversation) {
      applyMessageUpdate(message)
      if (shouldNotify) {
        markConversationAsRead(message.conversationId, [message.id]).catch(() => {})
      }
    } else if (shouldNotify) {
      incrementUnreadCounter(message.conversationId)
    }

    if (
      shouldNotify &&
      (!isSameConversation || (typeof document !== 'undefined' && (document.hidden || !document.hasFocus())))
    ) {
      if (typeof notifyNewIncomingMessage === 'function') {
        notifyNewIncomingMessage(message)
      }
    }
  }

  function connectRealtime(convId) {
    if (!authToken.value) {
      connectionStatus.value = 'idle'
      return
    }

    connectionStatus.value = 'connecting'
    socketRef.value = createConversationSocket(convId, {
      token: authToken.value,
      onOpen: () => (connectionStatus.value = 'connected'),
      onError: () => (connectionStatus.value = 'error'),
      onClose: () => (connectionStatus.value = 'idle'),
      onEvent: (payload) => {
        if (!payload || typeof payload !== 'object') return
        if (payload.event === 'ready') {
          connectionStatus.value = 'connected'
          return
        }
        if (payload.event === 'message' || payload.event === 'message.updated') {
          handleIncomingRealtime(payload)
        }
      },
    })
  }

  function disconnectRealtime() {
    if (socketRef.value) {
      socketRef.value.close()
      socketRef.value = null
    }
    connectionStatus.value = 'idle'
  }

  return {
    socketRef,
    connectionStatus,
    connectRealtime,
    disconnectRealtime,
    handleIncomingRealtime,
  }
}
