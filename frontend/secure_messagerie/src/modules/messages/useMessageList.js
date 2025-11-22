import { nextTick, reactive, ref } from 'vue'
import { api } from '@/utils/api'
import { normalizeMessage } from './mappers'

export function useMessageList({
  selectedConversationId,
  currentUserId,
  ensureMeta,
  extractError,
  scrollToBottom,
  messageError,
}) {
  const messageErrorRef = messageError ?? ref('')
  const scrollToBottomFn = typeof scrollToBottom === 'function' ? scrollToBottom : () => {}
  const messages = ref([])
  const pagination = reactive({
    beforeCursor: null,
    afterCursor: null,
    hasMoreBefore: false,
    hasMoreAfter: false,
  })
  const loadingMessages = ref(false)
  const loadingOlderMessages = ref(false)
  const suppressAutoScroll = ref(false)

  const paginationHeaderKeys = {
    before: 'x-pagination-before',
    after: 'x-pagination-after',
    hasBefore: 'x-pagination-has-before',
    hasAfter: 'x-pagination-has-after',
  }

  function readHeader(headers, name) {
    if (!headers) return null
    if (typeof headers.get === 'function') {
      const value = headers.get(name)
      if (value != null) return value
      return headers.get(name.toLowerCase())
    }
    const lower = name.toLowerCase()
    if (lower in headers) return headers[lower]
    const exact = Object.keys(headers).find((key) => key.toLowerCase() === lower)
    return exact ? headers[exact] : null
  }

  function updatePaginationFromHeaders(headers, context = {}) {
    const beforeHeader = readHeader(headers, paginationHeaderKeys.before)
    const afterHeader = readHeader(headers, paginationHeaderKeys.after)
    const hasBeforeHeader = readHeader(headers, paginationHeaderKeys.hasBefore)
    const hasAfterHeader = readHeader(headers, paginationHeaderKeys.hasAfter)

    const parseNumber = (value) => {
      if (value === null || value === undefined || value === '') return null
      const num = Number(value)
      return Number.isNaN(num) ? null : num
    }

    const parseBool = (value) => {
      if (typeof value === 'boolean') return value
      if (typeof value === 'string') {
        if (value.toLowerCase() === 'true') return true
        if (value.toLowerCase() === 'false') return false
      }
      return null
    }

    const before = parseNumber(beforeHeader)
    const after = parseNumber(afterHeader)
    const hasBefore = parseBool(hasBeforeHeader)
    const hasAfter = parseBool(hasAfterHeader)

    if (context.reset) {
      pagination.beforeCursor = before
      pagination.afterCursor = after
      pagination.hasMoreBefore = hasBefore ?? false
      pagination.hasMoreAfter = hasAfter ?? false
      return
    }

    if (context.before != null) {
      pagination.beforeCursor = before
      pagination.hasMoreBefore = hasBefore ?? pagination.hasMoreBefore
    } else if (context.after != null) {
      pagination.afterCursor = after
      pagination.hasMoreAfter = hasAfter ?? pagination.hasMoreAfter
    } else if (before !== null || after !== null || hasBefore !== null || hasAfter !== null) {
      pagination.beforeCursor = before
      pagination.afterCursor = after
      if (hasBefore !== null) pagination.hasMoreBefore = hasBefore
      if (hasAfter !== null) pagination.hasMoreAfter = hasAfter
    } else if (Array.isArray(context.received)) {
      const list = context.received
      pagination.beforeCursor = list.length ? list[0].streamPosition : null
      pagination.afterCursor = list.length ? list[list.length - 1].streamPosition : null
      pagination.hasMoreBefore = Boolean(context.before && list.length)
      pagination.hasMoreAfter = Boolean(context.after && list.length)
    }
  }

  async function loadMessages({
    conversationId = selectedConversationId.value,
    reset = false,
    before = null,
    after = null,
    limit = 50,
  } = {}) {
    if (!conversationId) return
    if (before && after) return
    if (reset) {
      loadingMessages.value = true
      messages.value = []
      pagination.beforeCursor = null
      pagination.afterCursor = null
      pagination.hasMoreBefore = false
      pagination.hasMoreAfter = false
    }
    messageErrorRef.value = ''
    try {
      const params = { limit }
      if (before) params.before = before
      if (after) params.after = after
      const response = await api.get(`/conversations/${conversationId}/messages`, { params })
      const list = Array.isArray(response.data)
        ? response.data.map((entry) => normalizeMessage(entry, { selfId: currentUserId.value }))
        : []
      updatePaginationFromHeaders(response.headers, { reset, before, after, received: list })
      if (reset) {
        messages.value = list
      } else if (before) {
        messages.value = [...list, ...messages.value]
      } else if (after) {
        messages.value = [...messages.value, ...list]
      } else {
        messages.value = list
      }
      const meta = ensureMeta(conversationId)
      if (list.length && !before) {
        const last = list[list.length - 1]
        meta.lastPreview = last.preview
        meta.lastActivity = last.createdAt
      }
    } catch (err) {
      if (reset) {
        messageErrorRef.value = extractError(err, 'Impossible de charger les messages.')
        messages.value = []
      }
    } finally {
      if (reset) {
        loadingMessages.value = false
        await nextTick()
        scrollToBottomFn()
      }
    }
  }

  async function loadOlderMessages() {
    if (
      loadingOlderMessages.value ||
      !pagination.hasMoreBefore ||
      pagination.beforeCursor == null ||
      !selectedConversationId.value
    ) {
      return
    }
    loadingOlderMessages.value = true
    suppressAutoScroll.value = true
    try {
      await loadMessages({
        conversationId: selectedConversationId.value,
        before: pagination.beforeCursor,
        limit: 50,
      })
    } finally {
      loadingOlderMessages.value = false
    }
  }

  async function ensureMessageVisible(messageId, streamPosition) {
    if (messages.value.some((msg) => msg.id === messageId)) return

    let guard = 0

    while (
      !messages.value.some((msg) => msg.id === messageId) &&
      pagination.hasMoreBefore &&
      pagination.beforeCursor
    ) {
      if (
        typeof streamPosition === 'number' &&
        pagination.beforeCursor !== null &&
        streamPosition >= pagination.beforeCursor
      ) {
        break
      }

      await loadOlderMessages()
      guard += 1
      if (guard > 20) break
    }
  }

  function applyMessageUpdate(nextMessage) {
    const idx = messages.value.findIndex((msg) => msg.id === nextMessage.id)
    if (idx === -1) {
      messages.value.push(nextMessage)
      return nextMessage
    }

    const current = messages.value[idx]
    const merged = {
      ...current,
      ...nextMessage,
      createdAt: nextMessage.createdAt || current.createdAt,
      deliveryState: nextMessage.deliveryState ?? current.deliveryState,
      deliveredAt: nextMessage.deliveredAt ?? current.deliveredAt,
      readAt: nextMessage.readAt ?? current.readAt,
      reactions: nextMessage.reactions || current.reactions,
      pinned: typeof nextMessage.pinned === 'boolean' ? nextMessage.pinned : current.pinned,
      pinnedAt: nextMessage.pinnedAt ?? current.pinnedAt,
      pinnedBy: nextMessage.pinnedBy ?? current.pinnedBy,
      security: nextMessage.security || current.security,
      preview: nextMessage.preview || current.preview,
      attachments: Array.isArray(nextMessage.attachments) ? nextMessage.attachments : current.attachments,
      editedAt: nextMessage.editedAt ?? current.editedAt,
      deletedAt: nextMessage.deletedAt ?? current.deletedAt,
      deleted: typeof nextMessage.deleted === 'boolean' ? nextMessage.deleted : current.deleted,
      replyTo: nextMessage.replyTo ?? current.replyTo,
      forwardFrom: nextMessage.forwardFrom ?? current.forwardFrom,
      streamPosition: nextMessage.streamPosition ?? current.streamPosition,
    }
    messages.value[idx] = merged

    return merged
  }

  function applyLocalReadReceipt(convId, ids = []) {
    const targetIds =
      Array.isArray(ids) && ids.length ? new Set(ids.map((id) => String(id))) : null
    const now = new Date()
    messages.value.forEach((message) => {
      if (String(message.conversationId) !== String(convId)) return
      if (message.sentByMe || message.deleted) return
      if (targetIds && !targetIds.has(String(message.id))) return
      if (message.deliveryState === 'read') return
      message.deliveryState = 'read'
      message.readAt = now
    })
  }

  return {
    messages,
    pagination,
    loadingMessages,
    loadingOlderMessages,
    suppressAutoScroll,
    loadMessages,
    loadOlderMessages,
    ensureMessageVisible,
    applyMessageUpdate,
    applyLocalReadReceipt,
  }
}
