import { reactive, ref } from 'vue'
import { api } from '@/utils/api'
import { normalizeConversation, normalizeMember, memberUserId } from '@/views/messages/mappers'

export function useConversationsState({
  route,
  selectConversation,
  currentUserId,
  selectedConversationId,
  applyLocalReadReceipt,
  extractError,
}) {
  const conversations = ref([])
  const conversationMeta = reactive({})
  const loadingConversations = ref(true)
  const conversationError = ref('')
  const unreadSummary = ref({ total: 0, conversations: [] })

  function initializeMeta(conv) {
    if (!conv?.id) return
    if (!conversationMeta[conv.id]) {
      conversationMeta[conv.id] = {
        unreadCount: 0,
        lastPreview: '',
        lastActivity: conv.createdAt,
        avatarUrl: conv.avatarUrl,
      }
    }
  }

  function ensureMeta(convId) {
    initializeMeta({ id: convId, createdAt: new Date(), avatarUrl: null })
    return conversationMeta[convId]
  }

  function applyUnreadMeta() {
    const map = new Map(
      unreadSummary.value.conversations.map((entry) => [String(entry.conversation_id), Number(entry.unread || 0)]),
    )
    conversations.value.forEach((conv) => {
      const meta = ensureMeta(conv.id)
      meta.unreadCount = map.get(conv.id) || 0
    })
  }

  async function loadUnreadSummary() {
    try {
      const { data } = await api.get('/messages/unread_summary')
      unreadSummary.value = {
        total: Number(data?.total || 0),
        conversations: Array.isArray(data?.conversations)
          ? data.conversations.map((entry) => ({
              conversation_id: String(entry.conversation_id),
              unread: Number(entry.unread || 0),
            }))
          : [],
      }
      applyUnreadMeta()
      emitUnreadSnapshot()
    } catch (err) {
      console.warn('Unable to load unread summary', err)
    }
  }

  function emitUnreadSnapshot() {
    if (typeof window === 'undefined') return
    try {
      const byConversation = unreadSummary.value.conversations.reduce((acc, entry) => {
        acc[entry.conversation_id] = entry.unread
        return acc
      }, {})
      const payload = {
        total: unreadSummary.value.total,
        by_conversation: byConversation,
      }
      window.dispatchEvent(new CustomEvent('cova:unread', { detail: payload }))
      localStorage.setItem('unread_counts', JSON.stringify(byConversation))
    } catch {}
  }

  function setUnreadForConversation(convId, newCount) {
    const entries = unreadSummary.value.conversations.slice()
    const idx = entries.findIndex((entry) => entry.conversation_id === convId)
    const previous = idx >= 0 ? Number(entries[idx].unread || 0) : 0
    if (newCount > 0) {
      const normalized = { conversation_id: convId, unread: newCount }
      if (idx >= 0) entries[idx] = normalized
      else entries.push(normalized)
    } else if (idx >= 0) {
      entries.splice(idx, 1)
    }
    const total = Math.max(unreadSummary.value.total - previous + Math.max(newCount, 0), 0)
    unreadSummary.value = {
      total,
      conversations: entries,
    }
    emitUnreadSnapshot()
  }

  async function markConversationAsRead(convId, ids = []) {
    if (!convId) return
    const meta = ensureMeta(convId)
    const uniqueIds = Array.isArray(ids) ? Array.from(new Set(ids.filter(Boolean))) : []
    if (uniqueIds.length) {
      const decrement = Math.min(uniqueIds.length, meta.unreadCount || 0)
      meta.unreadCount = Math.max((meta.unreadCount || 0) - decrement, 0)
      setUnreadForConversation(convId, meta.unreadCount)
    } else {
      meta.unreadCount = 0
      setUnreadForConversation(convId, 0)
    }
    const body = uniqueIds.length ? { message_ids: uniqueIds } : {}
    if (typeof applyLocalReadReceipt === 'function') {
      applyLocalReadReceipt(convId, uniqueIds)
    }
    try {
      await api.post(`/conversations/${convId}/read`, body)
    } catch (err) {
      console.warn('Unable to synchroniser la lecture', err)
    }
  }

  function incrementUnreadCounter(convId) {
    const meta = ensureMeta(convId)
    meta.unreadCount = (meta.unreadCount || 0) + 1
    setUnreadForConversation(convId, meta.unreadCount)
  }

  function applyConversationPatch(payload) {
    if (!payload) return
    const normalized = normalizeConversation(payload, { selfId: currentUserId.value })
    if (!normalized) return
    const idx = conversations.value.findIndex((conv) => conv.id === normalized.id)
    if (idx >= 0) {
      conversations.value[idx] = { ...conversations.value[idx], ...normalized }
    } else {
      conversations.value.push(normalized)
      initializeMeta(normalized)
    }
  }

  function applyMemberPayload(payload) {
    const normalized = normalizeMember(payload)
    if (!normalized) return
    const convId = selectedConversationId.value
    if (!convId) return
    const target = conversations.value.find((conv) => conv.id === convId)
    if (!target) return
    if (!Array.isArray(target.members)) {
      target.members = []
    }
    const idx = target.members.findIndex((member) => member.id === normalized.id)
    if (idx >= 0) {
      target.members[idx] = normalized
    } else {
      target.members.push(normalized)
    }
    const activeMembers = target.members.filter((member) => member.state === 'active')
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    target.participants = activeMembers.filter((member) => !selfId || memberUserId(member) !== selfId)
  }

  function updateConversationBlockStateByUser(userId, flags = {}) {
    if (!userId) return
    const target = String(userId)
    conversations.value.forEach((conv) => {
      if (conv.type !== 'direct' || !Array.isArray(conv.members)) return
      const hasUser = conv.members.some((member) => memberUserId(member) === target)
      if (!hasUser) return
      if (Object.prototype.hasOwnProperty.call(flags, 'blockedByMe')) {
        conv.blockedByMe = Boolean(flags.blockedByMe)
      }
      if (Object.prototype.hasOwnProperty.call(flags, 'blockedByOther')) {
        conv.blockedByOther = Boolean(flags.blockedByOther)
      }
    })
  }

  function onAvatarFailure(convId) {
    const meta = ensureMeta(convId)
    meta.avatarUrl = null
  }

  async function loadConversations() {
    loadingConversations.value = true
    conversationError.value = ''
    try {
      const { data } = await api.get('/conversations/')
      const selfId = currentUserId.value
      const list = Array.isArray(data)
        ? data.map((item) => normalizeConversation(item, { selfId })).filter(Boolean)
        : []
      conversations.value = list
      list.forEach((conv) => initializeMeta(conv))
      if (!selectedConversationId.value && list.length) {
        const initial = route.query.conversation ? String(route.query.conversation) : list[0].id
        await selectConversation(initial)
      }
      await loadUnreadSummary()
    } catch (err) {
      conversationError.value = extractError
        ? extractError(err, "Impossible de charger les conversations.")
        : "Impossible de charger les conversations."
    } finally {
      loadingConversations.value = false
    }
  }

  return {
    conversations,
    conversationMeta,
    loadingConversations,
    conversationError,
    unreadSummary,
    ensureMeta,
    loadConversations,
    loadUnreadSummary,
    setUnreadForConversation,
    markConversationAsRead,
    incrementUnreadCounter,
    applyConversationPatch,
    applyMemberPayload,
    updateConversationBlockStateByUser,
    onAvatarFailure,
  }
}
