import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/utils/api'
import {
  uploadAttachment,
  editConversationMessage,
  searchConversationMessages,
  updateConversation,
  leaveConversation,
  updateConversationMember,
  listConversationInvites,
  createConversationInvite,
  revokeConversationInvite,
} from '@/services/conversations'
import { defaultGifLibrary } from '@/utils/reactions'
import {
  formatAbsolute,
  formatFileSize,
  formatListTime,
  formatTime,
  messagePreviewText,
  extractDeliverySummary,
} from './formatters'
import { generateLocalId } from './id'
import { useMessageSearch } from './useMessageSearch'
import { useComposerTools } from './useComposerTools'
import { useNotificationsManager } from './useNotificationsManager'
import { useConversationFilters } from './useConversationFilters'
import { useMessageActions } from './useMessageActions'
import { useDeleteMessage } from './useDeleteMessage'
import { useRealtimeMessaging } from './useRealtimeMessaging'

export function useMessagesView() {
  const STATUS_LABELS = {
    available: 'Disponible',
    online: 'En ligne',
    busy: 'Occupé',
    away: 'Absent',
    dnd: 'Ne pas déranger',
    offline: 'Hors ligne',
  }

  const gifLibrary = defaultGifLibrary
  const stripDiacritics = (value = '') => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')

  const conversations = ref([])

  const conversationMeta = reactive({})
  const loadingConversations = ref(true)
  const conversationError = ref('')
  const unreadSummary = ref({ total: 0, conversations: [] })
  const {
    conversationSearch,
    conversationFilter,
    conversationFilters,
    conversationRoles,
    conversationSummary,
    sortedConversations,
    activeFilterLabel,
  } = useConversationFilters({
    conversations,
    conversationMeta,
    loadingConversations,
  })
  const showConversationPanel = ref(false)
  const conversationForm = reactive({ title: '', topic: '', archived: false })
  const savingConversation = ref(false)
  const conversationInfoError = ref('')
  const invites = ref([])
  const loadingInvites = ref(false)
  const selectedConversationId = ref(null)
  const messages = ref([])

  const inviteBusy = ref(false)
  const inviteRevokeBusy = reactive({})
  const memberBusy = reactive({})
  const leavingConversation = ref(false)
  const pagination = reactive({
    beforeCursor: null,
    afterCursor: null,
    hasMoreBefore: false,
    hasMoreAfter: false,
  })
  const loadingOlderMessages = ref(false)
  const suppressAutoScroll = ref(false)

  const {
    showSearchPanel,
    messageSearch,
    toggleSearchPanel,
    closeSearchPanel,
    resetSearchPanel,
    performMessageSearch,
    jumpToSearchResult,
  } = useMessageSearch({
    stripDiacritics,
    normalizeMessage,
    searchConversationMessages,
    messages,
    selectedConversationId,
    ensureMessageVisible,
    selectConversation,
    scrollToMessage,
    extractError,
  })


  const inviteForm = reactive({ email: '', role: 'member', expiresInHours: 72 })
  const loadingMessages = ref(false)

  const messageError = ref('')

  const messageInput = ref('')
  const composerTools = useComposerTools({
    gifLibrary,
    selectedConversationId,
    uploadAttachment,
    extractError,
    messageInput,
  })

  const {
    attachmentInput,
    pendingAttachments,
    attachmentError,
    composerState,
    showPicker,
    pickerMode,
    emojiSearch,
    gifSearch,
    gifResults,
    filteredEmojiSections,
    displayedGifs,
    loadingGifs,
    gifError,
    gifSearchAvailable,
    togglePicker,
    setPickerMode,
    resetComposerState,
    startReply,
    startForward,
    startEdit,
    cancelComposerContext,
    triggerAttachmentPicker,
    onAttachmentChange,
    queueAttachment,
    uploadAttachmentFile,
    removeAttachment,
    clearPendingAttachments,
  } = composerTools

  const {
    messageToasts,
    browserNotificationsEnabled,
    notificationPermissionRequestPending,
    queueToastNotification,
    dismissToast,
    openToastConversation,
    notifyNewIncomingMessage,
    triggerBrowserNotification,
    handleBrowserPrefStorage,
    handleBrowserPrefBroadcast,
    syncBrowserNotificationPreference,
    clearNotificationTimers,
  } = useNotificationsManager({
    selectedConversationId,
    selectConversation,
    ensureMessageVisible,
    messagePreviewText,
    generateLocalId,
  })

  const forwardPicker = reactive({
    open: false,
    message: null,
    query: '',
  })
  const forwardPickerInput = ref(null)

  const forwardPickerTargets = computed(() => {
    const term = forwardPicker.query.trim().toLowerCase()
    return conversations.value
      .filter((conv) => conv.id !== selectedConversationId.value)
      .filter((conv) => {
        if (!term) return true
        const name = conv.displayName?.toLowerCase() || ''
        if (name.includes(term)) return true
        return conv.members.some((member) =>
          (member.displayName || member.email || '').toLowerCase().includes(term),
        )
      })
      .slice(0, 12)
  })

  function initiateForward(message) {
    if (!message) return
    forwardPicker.message = message
    forwardPicker.query = ''
    forwardPicker.open = true
    nextTick(() => {
      forwardPickerInput.value?.focus()
    })
  }

  function cancelForwardSelection() {
    forwardPicker.open = false
    forwardPicker.message = null
    forwardPicker.query = ''
  }

  async function confirmForwardTarget(conversationId) {
    if (!conversationId || !forwardPicker.message) return
    await selectConversation(conversationId)
    startForward(forwardPicker.message)
    cancelForwardSelection()
  }

  const sending = ref(false)
  const reactionPalette = [
    '\u{1F44D}',
    '\u{2764}\u{FE0F}',
    '\u{1F389}',
    '\u{1F44F}',
    '\u{1F525}',
    '\u{1F604}',
    '\u{1F64F}',
    '\u{1F440}',
    '\u{1F680}',
    '\u{2757}',
  ]

  const route = useRoute()
  const router = useRouter()
  const messageScroller = ref(null)

  const currentUserId = ref(localStorage.getItem('user_id') || null)
  const authToken = ref(localStorage.getItem('access_token') || null)

  const {
    cloneComposerReference,
    mapOptimisticAttachments,
    removeMessageById,
    resolveOptimisticMessage,
    reactionPickerFor,
    messageMenuOpen,
    toggleReactionPicker,
    toggleMessageMenu,
    closeTransientMenus,
    handlePinToggle,
    handleReactionSelection,
    togglePin,
    toggleReaction,
    isPinning,
    isReactionPending,
    optimisticMessageIds,
    copyMessage,
    copiedMessageId,
    downloadAttachment,
    messageFormatters,
  } = useMessageActions({
    messages,
    selectedConversationId,
    currentUserId,
    messageError,
    applyMessageUpdate,
    normalizeMessage,
    extractError,
    messagePreviewText,
    formatTime,
    formatAbsolute,
    formatFileSize,
    extractDeliverySummary,
  })

  const {
    messageStatusLabel,
    messageStatusClass,
    messageStatusDetail,
    messageSecurityLabel,
    messageSecurityTooltip,
  } = messageFormatters

  const {
    deleteDialog,
    deleteDialogPreview,
    confirmDeleteMessage,
    closeDeleteDialog,
    performDeleteMessage,
  } = useDeleteMessage({
    selectedConversationId,
    messagePreviewText,
    applyMessageUpdate,
    normalizeMessage,
    extractError,
  })

  const {
    socketRef,
    connectionStatus,
    connectRealtime,
    disconnectRealtime,
    handleIncomingRealtime,
  } = useRealtimeMessaging({
    authToken,
    normalizeMessage,
    ensureMeta,
    pagination,
    selectedConversationId,
    applyMessageUpdate,
    markConversationAsRead,
    incrementUnreadCounter,
    notifyNewIncomingMessage,
  })


  function computeInitials(label = '') {
    if (!label) return 'C'
    const tokens = String(label)
      .trim()
      .split(/\s+/)
      .filter(Boolean)
    if (!tokens.length) return 'C'
    const first = tokens[0][0] || ''
    const second = tokens.length > 1 ? tokens[tokens.length - 1][0] : tokens[0][1] || ''
    const initials = (first + (second || '')).toUpperCase()
    return initials || 'C'
  }

  function normalizeMember(member) {
    if (!member) return null
    const id = member.user_id || member.id || member.member_id
    if (!id) return null
    const displayName = member.display_name || member.email || 'Membre'
    const userId = member.user_id || member.userId || member.contact_user_id || id
    return {
      id: String(id),
      userId: userId ? String(userId) : String(id),
      role: member.role || 'member',
      state: member.state || 'active',
      joinedAt: member.joined_at ? new Date(member.joined_at) : null,
      mutedUntil: member.muted_until ? new Date(member.muted_until) : null,
      displayName,
      email: member.email || '',
      avatarUrl: member.avatar_url || null,
      initials: computeInitials(displayName),
      presence: {
        status: member.presence_status || member.state || 'offline',
        lastSeen: member.last_seen ? new Date(member.last_seen) : null,
      },
    }
  }

  function normalizeConversation(payload) {
    if (!payload) return null
    const members = Array.isArray(payload.members)
      ? payload.members.map((member) => normalizeMember(member)).filter(Boolean)
      : []
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    const activeParticipants = members.filter(
      (member) => member.state === 'active' && (!selfId || member.id !== selfId),
    )
    const createdAt = payload.created_at ? new Date(payload.created_at) : new Date()
    let displayName = payload.title ? String(payload.title).trim() : ''
    if (!displayName) {
      const names = activeParticipants
        .map((member) => member.displayName || member.email)
        .filter(Boolean)
      displayName = names.join(', ')
    }
    if (!displayName) {
      displayName = members.length > 1 ? 'Conversation' : 'Nouvelle conversation'
    }
    return {
      id: String(payload.id),
      title: payload.title || null,
      topic: payload.topic || null,
      type: payload.type || 'group',
      archived: Boolean(payload.archived),
      createdAt,
      members,
      participants: activeParticipants,
      displayName,
      initials: computeInitials(displayName),
      avatarUrl: payload.avatar_url || null,
    }
  }


  const selectedConversation = computed(() => {
    if (!selectedConversationId.value) return null
    return conversations.value.find((conv) => conv.id === selectedConversationId.value) || null
  })

  const headerParticipants = computed(() => {
    const conv = selectedConversation.value
    if (!conv || !Array.isArray(conv.participants)) return ''
    const names = conv.participants
      .map((participant) => participant.displayName || participant.email)
      .filter(Boolean)
    return names.join(', ')
  })

  function normalizePresenceStatus(status) {
    const value = String(status || '').toLowerCase()
    if (['available', 'online', 'active'].includes(value)) return 'available'
    if (['busy', 'occupied'].includes(value)) return 'busy'
    if (value === 'away') return 'away'
    if (['dnd', 'do_not_disturb'].includes(value)) return 'dnd'
    return 'offline'
  }

  function memberPresence(userId) {
    if (!userId) return { status: 'offline', label: STATUS_LABELS.offline, lastSeen: null }
    const conv = selectedConversation.value
    if (!conv || !Array.isArray(conv.members)) {
      return { status: 'offline', label: STATUS_LABELS.offline, lastSeen: null }
    }
    const members = conv.members
    const target =
      members.find((member) => member.id === String(userId)) ||
      members.find((member) => member.userId === String(userId))
    if (!target) {
      return { status: 'offline', label: STATUS_LABELS.offline, lastSeen: null }
    }
    const rawStatus = target.presence?.status || target.state
    const status = normalizePresenceStatus(rawStatus)
    const lastSeenRaw = target.presence?.lastSeen || target.presence?.last_seen || target.lastSeen || target.last_seen
    return {
      status,
      label: STATUS_LABELS[status] || STATUS_LABELS.offline,
      lastSeen: lastSeenRaw ? new Date(lastSeenRaw) : null,
    }
  }

  function memberPresenceText(userId) {
    const presence = memberPresence(userId)
    if (presence.status === 'available') return STATUS_LABELS.available
    if (presence.status === 'busy') return 'Occupé'
    if (presence.status === 'away') return 'Absent'
    if (presence.status === 'dnd') return 'Ne pas déranger'
    if (presence.lastSeen) {
      return `Vu ${formatTime(presence.lastSeen)}`
    }
    return presence.label
  }

  const primaryParticipantPresence = computed(() => {
    const conv = selectedConversation.value
    if (!conv) {
      return { status: 'offline', label: STATUS_LABELS.offline, lastSeen: null }
    }
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    const target =
      conv.members?.find((member) => member.id !== selfId) ||
      conv.participants?.find((member) => member.id !== selfId)
    if (!target) {
      return { status: 'offline', label: STATUS_LABELS.offline, lastSeen: null }
    }
    return memberPresence(target.id || target.userId)
  })

  const headerSubtitle = computed(() => {
    const conv = selectedConversation.value
    if (!conv) return ''
    const parts = [headerParticipants.value]
    if (conv.type === 'direct') {
      parts.push(primaryParticipantPresence.value.label)
    } else if (conv.topic) {
      parts.push(conv.topic)
    }
    return parts.filter(Boolean).join(' · ')
  })

  const currentMembership = computed(() => {
    const conv = selectedConversation.value
    if (!conv || !Array.isArray(conv.members)) return null
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    if (!selfId) return null
    return conv.members.find((member) => member.id === selfId) || null
  })

  const isConversationOwner = computed(() => currentMembership.value?.role === 'owner')
  const canManageConversation = computed(() => isConversationOwner.value)
  const readyAttachments = computed(() => pendingAttachments.value.filter((entry) => entry.status === 'ready'))
  const hasAttachmentInProgress = computed(() => pendingAttachments.value.some((entry) => entry.status === 'uploading'))
  const isEditingMessage = computed(() => composerState.mode === 'edit' && Boolean(composerState.targetMessageId))
  const hasComposerContext = computed(() => {
    return (
      composerState.mode !== 'new' ||
      composerState.replyTo !== null ||
      composerState.forwardFrom !== null
    )
  })


  const pinnedMessages = computed(() => {
    return messages.value
      .filter((message) => message.pinned)
      .sort((a, b) => {

        const aDate = (a.pinnedAt || a.createdAt).getTime()

        const bDate = (b.pinnedAt || b.createdAt).getTime()

        return bDate - aDate

      })

  })





  const canSend = computed(() => {
    const value = messageInput.value.trim()
    const attachmentsReady = readyAttachments.value.length > 0 && !isEditingMessage.value
    return (Boolean(value) || attachmentsReady || composerState.mode === 'reply' || composerState.mode === 'forward') &&
      value.length <= 2000 &&
      Boolean(selectedConversationId.value)
  })


  const connectionStatusClass = computed(() => {

    switch (connectionStatus.value) {

      case 'connected':

        return 'ok'

      case 'connecting':

        return 'pending'

      default:

        return 'error'

    }

  })



  const connectionStatusLabel = computed(() => {
    switch (connectionStatus.value) {

      case 'connected':

        return 'Canal temps r+®el actif'

      case 'connecting':

        return 'ConnexionÔÇª'

      case 'error':

        return 'Canal indisponible'

      default:

        return 'En veille'

    }

  })



  watch(
    () => route.query.conversation,
    (id) => {
      if (!id) return
      const convId = String(id)
      if (conversations.value.some((conv) => conv.id === convId)) {
        selectConversation(convId)
      }
    },
  )

  watch(selectedConversationId, (id) => {
    closeTransientMenus()
    if (!id) {
      showConversationPanel.value = false
      invites.value = []
      clearPendingAttachments()
      resetComposerState()
      resetSearchPanel()
      return
    }
    router.replace({ query: { ...route.query, conversation: id } }).catch(() => {})
    emitActiveConversation(id)
    resetComposerState()
    resetSearchPanel()
    if (showConversationPanel.value) {
      syncConversationFormFromSelected()
      if (canManageConversation.value) {
        loadConversationInvites(id)
      } else {
        invites.value = []
      }
    }
  })

  watch(showConversationPanel, (open) => {
    if (open) {
      syncConversationFormFromSelected()
      if (canManageConversation.value && selectedConversationId.value) {
        loadConversationInvites(selectedConversationId.value)
      } else {
        invites.value = []
      }
    }
  })

  watch(canManageConversation, (canManage) => {
    if (!showConversationPanel.value) return
    if (canManage && selectedConversationId.value) {
      loadConversationInvites(selectedConversationId.value)
    } else {
      invites.value = []
    }
  })

  watch(
    () => messages.value.length,
    async () => {
      await nextTick()
      if (suppressAutoScroll.value) {
        suppressAutoScroll.value = false
        return
      }
      if (!loadingOlderMessages.value) {
        scrollToBottom()
      }
    },
  )

  async function loadConversations() {
    loadingConversations.value = true
    conversationError.value = ''
    try {
      const { data } = await api.get('/conversations/')
      const list = Array.isArray(data) ? data.map((item) => normalizeConversation(item)).filter(Boolean) : []
      conversations.value = list
      list.forEach((conv) => initializeMeta(conv))
      if (!selectedConversationId.value && list.length) {
        const initial = route.query.conversation ? String(route.query.conversation) : list[0].id
        await selectConversation(initial)
      }
      await loadUnreadSummary()

    } catch (err) {

      conversationError.value = extractError(err, "Impossible de charger les conversations.")

    } finally {

      loadingConversations.value = false

    }

  }



  async function loadUnreadSummary() {

    try {

      const { data } = await api.get('/messages/unread_summary')

      unreadSummary.value = {

        total: Number(data?.total || 0),

        conversations: Array.isArray(data?.conversations) ? data.conversations.map((entry) => ({

          conversation_id: String(entry.conversation_id),

          unread: Number(entry.unread || 0),

        })) : [],

      }

      applyUnreadMeta()

    } catch (err) {

      console.warn('Unable to load unread summary', err)

    }

  }



async function loadMessages({ conversationId = selectedConversationId.value, reset = false, before = null, after = null, limit = 50 } = {}) {
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
    messageError.value = ''
    try {
      const params = { limit }
      if (before) params.before = before
      if (after) params.after = after
      const response = await api.get(`/conversations/${conversationId}/messages`, { params })
      const list = Array.isArray(response.data) ? response.data.map(normalizeMessage) : []
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
      if (!before) {
        const readableIds = list
          .filter((message) => !message.sentByMe && !message.isSystem && !message.deleted)
          .map((message) => message.id)
        if (readableIds.length) {
          await markConversationAsRead(conversationId, readableIds)
        } else if (reset) {
          await loadUnreadSummary()
        }
      }
    } catch (err) {
      if (reset) {
        messageError.value = extractError(err, "Impossible de charger les messages.")
        messages.value = []
      }
    } finally {
      if (reset) {
        loadingMessages.value = false
        await nextTick()
        scrollToBottom()
      }
    }
  }
  async function loadOlderMessages() {
    if (
      loadingOlderMessages.value ||
      !selectedConversationId.value ||
      !pagination.hasMoreBefore ||
      !pagination.beforeCursor
    ) {
      return
    }
    loadingOlderMessages.value = true
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

  async function ensureMessageVisible(messageId, streamPosition) {
    if (messages.value.some((msg) => msg.id === messageId)) return

    let guard = 0

    while (

      !messages.value.some((msg) => msg.id === messageId) &&

      pagination.hasMoreBefore &&

      pagination.beforeCursor

    ) {

      if (typeof streamPosition === 'number' && pagination.beforeCursor !== null && streamPosition >= pagination.beforeCursor) {

        break

      }

      await loadOlderMessages()

      guard += 1

      if (guard > 20) break

    }
  }


  function normalizeMessage(payload, { selfId } = {}) {
    const convId = String(payload.conversation_id || payload.conv_id || '')
    const authorId = payload.author_id ? String(payload.author_id) : null
    const viewerId = selfId ?? (currentUserId.value ? String(currentUserId.value) : null)
    const createdAt = payload.created_at ? new Date(payload.created_at) : new Date()
    const displayName =
      payload.author_display_name || (authorId && viewerId && authorId === viewerId ? 'Vous' : 'Participant')

    const content = (payload.content || '').toString()

    const reactions = Array.isArray(payload.reactions)

      ? payload.reactions.map((reaction) => ({

          emoji: reaction.emoji,

          count: Number(reaction.count || 0),

          reacted: Boolean(reaction.reacted),

        }))

      : []

    const deliveredAt = payload.delivered_at ? new Date(payload.delivered_at) : null
    const readAt = payload.read_at ? new Date(payload.read_at) : null
    const pinnedAt = payload.pinned_at ? new Date(payload.pinned_at) : null
    const attachments = Array.isArray(payload.attachments)
      ? payload.attachments.map((attachment) => mapAttachmentPayload(attachment)).filter(Boolean)
      : []
    const editedAt = payload.edited_at ? new Date(payload.edited_at) : null
    const deletedAt = payload.deleted_at ? new Date(payload.deleted_at) : null
    const deleted = Boolean(payload.deleted)
    const replyTo = payload.reply_to ? mapReferencePayload(payload.reply_to) : null
    const forwardFrom = payload.forward_from ? mapReferencePayload(payload.forward_from) : null
    const streamPosition = Number(payload.stream_position ?? payload.streamPosition ?? null)
    return {
      id: String(payload.id || payload.message_id || generateLocalId()),
      conversationId: convId,
      authorId,
      displayName,
      avatarUrl: payload.author_avatar_url || null,
      content: deleted ? '' : content,
      createdAt,
      isSystem: Boolean(payload.is_system),
      sentByMe: Boolean(authorId && viewerId && authorId === viewerId),
      deliveryState: payload.delivery_state || null,
      deliveredAt,
      readAt,
      reactions,
      pinned: Boolean(payload.pinned),
      pinnedAt,
      pinnedBy: payload.pinned_by ? String(payload.pinned_by) : null,
      security: {
        scheme: payload.encryption_scheme || 'confidentiel',
        metadata: payload.encryption_metadata || {},
      },
      preview: `${displayName}: ${content}`.trim(),
      attachments,
      editedAt,
      deletedAt,
      deleted,
      replyTo,
      forwardFrom,
      streamPosition,
    }
  }

  function mapAttachmentPayload(raw) {
    if (!raw) return null

    return {

      id: String(raw.id || raw.attachment_id || generateLocalId()),

      fileName: raw.file_name || raw.filename || raw.name || 'Pi+¿ce jointe',

      mimeType: raw.mime_type || raw.mimeType || null,

      sizeBytes: raw.size_bytes || raw.sizeBytes || null,

      sha256: raw.sha256 || null,

      downloadUrl: raw.download_url || raw.downloadUrl || null,

      encryption: raw.encryption || {},

    }

  }



  function mapReferencePayload(raw) {

    if (!raw) return null

    return {

      id: String(raw.id || raw.message_id || generateLocalId()),

      authorDisplayName: raw.author_display_name || 'Participant',

      excerpt: raw.excerpt || '',

      createdAt: raw.created_at ? new Date(raw.created_at) : null,

      deleted: Boolean(raw.deleted),

      attachments: Number(raw.attachments || 0),

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



  function initializeMeta(conv) {

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

    const map = new Map(unreadSummary.value.conversations.map((entry) => [String(entry.conversation_id), Number(entry.unread || 0)]))

    conversations.value.forEach((conv) => {

      const meta = ensureMeta(conv.id)

      meta.unreadCount = map.get(conv.id) || 0

    })

  }



  async function selectConversation(convId) {
    const id = String(convId)
    if (!conversations.value.some((conv) => conv.id === id)) return
    const isSame = selectedConversationId.value === id
    selectedConversationId.value = id
    messageInput.value = ''
    showPicker.value = false
    emojiSearch.value = ''
    gifSearch.value = ''
    gifError.value = ''
    loadingGifs.value = false
    gifResults.value = gifLibrary.slice()
    pickerMode.value = 'emoji'
    clearPendingAttachments()
    resetComposerState()
    messages.value = []
    disconnectRealtime()
    await loadMessages({ conversationId: id, reset: true })
    connectRealtime(id)
    if (!isSame) {
      await loadUnreadSummary()
    }
  }

  async function markConversationAsRead(convId, ids = []) {
    if (!convId) return
    const meta = ensureMeta(convId)
    const uniqueIds = Array.isArray(ids) ? Array.from(new Set(ids.filter(Boolean))) : []
    if (uniqueIds.length) {
      const decrement = Math.min(uniqueIds.length, meta.unreadCount || 0)
      meta.unreadCount = Math.max((meta.unreadCount || 0) - decrement, 0)
    } else {
      meta.unreadCount = 0
    }
    const body = uniqueIds.length ? { message_ids: uniqueIds } : {}
    applyLocalReadReceipt(convId, uniqueIds)
    try {
      await api.post(`/conversations/${convId}/read`, body)
    } catch (err) {
      console.warn('Unable to synchroniser la lecture', err)
    }
    await loadUnreadSummary()
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



  function incrementUnreadCounter(convId) {
    const meta = ensureMeta(convId)
    meta.unreadCount = (meta.unreadCount || 0) + 1
    const entries = unreadSummary.value.conversations.slice()
    const idx = entries.findIndex((entry) => entry.conversation_id === convId)
    if (idx >= 0) {

      entries[idx] = { ...entries[idx], unread: entries[idx].unread + 1 }

    } else {

      entries.push({ conversation_id: convId, unread: 1 })

    }

    unreadSummary.value = {
      total: unreadSummary.value.total + 1,
      conversations: entries,
    }
  }

  function applyConversationPatch(payload) {
    if (!payload) return
    const normalized = normalizeConversation(payload)
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
    target.participants = activeMembers.filter((member) => !selfId || member.id !== selfId)
  }

  function mapInvite(invite) {
    if (!invite) return null
    return {
      id: invite.id,
      email: invite.email,
      role: invite.role,
      token: invite.token,
      expiresAt: invite.expires_at ? new Date(invite.expires_at) : null,
      acceptedAt: invite.accepted_at ? new Date(invite.accepted_at) : null,
    }
  }

  function roleLabel(role) {
    const option = conversationRoles.find((entry) => entry.value === role)
    return option ? option.label : role
  }

  function limitDraft() {

    if (messageInput.value.length > 2000) {

      messageInput.value = messageInput.value.slice(0, 2000)

    }

  }



  async function sendMessage() {
    if (!selectedConversationId.value || !canSend.value) return
    if (composerState.mode === 'edit' && composerState.targetMessageId) {
      await submitMessageEdit()
      return
    }
    if (hasAttachmentInProgress.value) {
      attachmentError.value = 'S+®lectionnez une conversation avant d\'ajouter un fichier.'
      return
    }
    if (pendingAttachments.value.some((entry) => entry.status === 'error')) {
      attachmentError.value = 'Retirez ou renvoyez les fichiers en erreur avant l\'envoi.'
      return
    }
    attachmentError.value = ''
    const attachmentsPayload = readyAttachments.value
      .map((entry) => entry.descriptor?.upload_token)
      .filter(Boolean)
      .map((token) => ({ upload_token: token }))
    const draftContent = messageInput.value.trim()
    const payload = {
      content: draftContent,
      attachments: attachmentsPayload,
      reply_to_message_id: composerState.replyTo ? composerState.replyTo.id : null,
      forward_message_id: composerState.forwardFrom ? composerState.forwardFrom.id : null,
    }
    const optimisticId = generateLocalId()
    const optimisticMessage = {
      id: optimisticId,
      conversationId: selectedConversationId.value,
      content: draftContent,
      preview: draftContent.slice(0, 120),
      displayName: 'Vous',
      sentByMe: true,
      createdAt: new Date(),
      deliveryState: 'queued',
      reactions: [],
      pinned: false,
      pinnedAt: null,
      pinnedBy: null,
      isSystem: false,
      deleted: false,
      attachments: mapOptimisticAttachments(readyAttachments.value),
      replyTo: cloneComposerReference(composerState.replyTo),
      forwardFrom: cloneComposerReference(composerState.forwardFrom),
      localOnly: true,
    }
    messages.value.push(optimisticMessage)
    optimisticMessageIds.add(optimisticId)
    const previousInputValue = messageInput.value
    messageInput.value = ''
    await nextTick()
    scrollToBottom()
    sending.value = true
    try {
      const { data } = await api.post(`/conversations/${selectedConversationId.value}/messages`, payload)
      const message = normalizeMessage(data)
      message.sentByMe = true
      resolveOptimisticMessage(optimisticId, message)
      showPicker.value = false
      emojiSearch.value = ''
      gifSearch.value = ''
      gifError.value = ''
      loadingGifs.value = false
      gifResults.value = gifLibrary.slice()
      pickerMode.value = 'emoji'
      clearPendingAttachments()
      resetComposerState()
      const meta = ensureMeta(selectedConversationId.value)
      meta.lastPreview = message.preview
      meta.lastActivity = message.createdAt
      meta.unreadCount = 0
      await loadUnreadSummary()
    } catch (err) {
      optimisticMessageIds.delete(optimisticId)
      removeMessageById(optimisticId)
      messageInput.value = previousInputValue
      messageError.value = extractError(err, "Impossible d'envoyer le message.")
    } finally {
      sending.value = false
    }
  }

  async function submitMessageEdit() {
    if (!selectedConversationId.value || !composerState.targetMessageId) return
    sending.value = true
    try {
      const data = await editConversationMessage(selectedConversationId.value, composerState.targetMessageId, {
        content: messageInput.value.trim(),
      })
      const message = normalizeMessage(data)
      message.sentByMe = true
      applyMessageUpdate(message)
      messageInput.value = ''
      resetComposerState()
      showPicker.value = false
    } catch (err) {
      messageError.value = extractError(err, 'Impossible de modifier le message.')
    } finally {
      sending.value = false
    }
  }


  function onThreadScroll() {
    const el = messageScroller.value
    if (!el || loadingOlderMessages.value || !pagination.hasMoreBefore) return
    if (el.scrollTop < 120) {
      loadOlderMessages()
    }
  }

  function scrollToBottom() {
    const el = messageScroller.value
    if (el) el.scrollTop = el.scrollHeight
  }


  function onAvatarFailure(convId) {

    const meta = ensureMeta(convId)

    meta.avatarUrl = null

  }



  function emitActiveConversation(convId) {

    window.dispatchEvent(new CustomEvent('cova:active-conversation', { detail: { convId } }))

  }



  function goToNewConversation() {

    router.push({ path: '/dashboard/messages/new' }).catch(() => {})

  }



  function syncConversationFormFromSelected() {
    const conv = selectedConversation.value
    if (!conv) return
    conversationForm.title = conv.title || ''
    conversationForm.topic = conv.topic || ''
    conversationForm.archived = Boolean(conv.archived)
  }

  async function openConversationPanel() {
    if (!selectedConversation.value) return
    conversationInfoError.value = ''
    syncConversationFormFromSelected()
    showConversationPanel.value = true
    if (canManageConversation.value && selectedConversationId.value) {
      await loadConversationInvites(selectedConversationId.value)
    }
  }

  function closeConversationPanel() {
    showConversationPanel.value = false
    invites.value = []
  }

  async function saveConversationSettings() {
    if (!selectedConversationId.value) return
    savingConversation.value = true
    conversationInfoError.value = ''
    try {
      const payload = {
        title: conversationForm.title.trim() || null,
        topic: conversationForm.topic.trim() || null,
        archived: conversationForm.archived,
      }
      const data = await updateConversation(selectedConversationId.value, payload)
      applyConversationPatch(data)
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible d'enregistrer la conversation.")
    } finally {
      savingConversation.value = false
    }
  }

  async function leaveCurrentConversation() {
    if (!selectedConversationId.value) return
    leavingConversation.value = true
    conversationInfoError.value = ''
    const convId = selectedConversationId.value
    try {
      await leaveConversation(convId)
      conversations.value = conversations.value.filter((conv) => conv.id !== convId)
      delete conversationMeta[convId]
      showConversationPanel.value = false
      messages.value = []
      disconnectRealtime()
      selectedConversationId.value = null
      const fallback = conversations.value[0]
      if (fallback) {
        selectConversation(fallback.id)
      }
    } catch (err) {
      conversationInfoError.value = extractError(err, 'Impossible de quitter la conversation.')
    } finally {
      leavingConversation.value = false
    }
  }

  async function loadConversationInvites(convId) {
    if (!canManageConversation.value || !convId) {
      invites.value = []
      return
    }
    loadingInvites.value = true
    conversationInfoError.value = ''
    try {
      const data = await listConversationInvites(convId)
      invites.value = Array.isArray(data) ? data.map((invite) => mapInvite(invite)).filter(Boolean) : []
    } catch (err) {
      conversationInfoError.value = extractError(err, 'Impossible de charger les invitations.')
    } finally {
      loadingInvites.value = false
    }
  }

  async function submitInvite() {
    if (!selectedConversationId.value || !inviteForm.email.trim()) return
    inviteBusy.value = true
    conversationInfoError.value = ''
    try {
      const payload = {
        email: inviteForm.email.trim(),
        role: inviteForm.role,
        expires_in_hours: inviteForm.expiresInHours,
      }
      const data = await createConversationInvite(selectedConversationId.value, payload)
      const mapped = mapInvite(data)
      if (mapped) {
        invites.value = [mapped, ...invites.value]
      }
      inviteForm.email = ''
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible de cr+®er l'invitation.")
    } finally {
      inviteBusy.value = false
    }
  }

  async function revokeInvite(inviteId) {
    if (!selectedConversationId.value || !inviteId) return
    inviteRevokeBusy[inviteId] = true
    conversationInfoError.value = ''
    try {
      await revokeConversationInvite(selectedConversationId.value, inviteId)
      invites.value = invites.value.filter((invite) => invite.id !== inviteId)
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible de r+®voquer l'invitation.")
    } finally {
      delete inviteRevokeBusy[inviteId]
    }
  }

  function formatInviteStatus(invite) {
    if (!invite) return ''
    if (invite.acceptedAt) {
      return `Accept+®e ${formatAbsolute(invite.acceptedAt)}`
    }
    if (invite.expiresAt) {
      return `Expire ${formatAbsolute(invite.expiresAt)}`
    }
    return ''
  }

  async function updateMemberRole(member, role) {
    if (!selectedConversationId.value || !member?.id || !role || member.role === role) return
    memberBusy[member.id] = true
    conversationInfoError.value = ''
    try {
      const data = await updateConversationMember(selectedConversationId.value, member.id, { role })
      applyMemberPayload(data)
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible de mettre +á jour le membre.")
    } finally {
      delete memberBusy[member.id]
    }
  }

  async function muteMember(member, minutes = 60) {
    if (!selectedConversationId.value || !member?.id) return
    memberBusy[member.id] = true
    conversationInfoError.value = ''
    const mutedUntil = new Date(Date.now() + minutes * 60000).toISOString()
    try {
      const data = await updateConversationMember(selectedConversationId.value, member.id, { muted_until: mutedUntil })
      applyMemberPayload(data)
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible de mettre le membre en sourdine.")
    } finally {
      delete memberBusy[member.id]
    }
  }

  async function unmuteMember(member) {
    if (!selectedConversationId.value || !member?.id) return
    memberBusy[member.id] = true
    conversationInfoError.value = ''
    try {
      const data = await updateConversationMember(selectedConversationId.value, member.id, { muted_until: null })
      applyMemberPayload(data)
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible de r+®tablir le membre.")
    } finally {
      delete memberBusy[member.id]
    }
  }

  async function removeMember(member) {
    if (!selectedConversationId.value || !member?.id) return
    memberBusy[member.id] = true
    conversationInfoError.value = ''
    try {
      const data = await updateConversationMember(selectedConversationId.value, member.id, { state: 'left' })
      applyMemberPayload(data)
    } catch (err) {
      conversationInfoError.value = extractError(err, 'Impossible de retirer le membre.')
    } finally {
      delete memberBusy[member.id]
    }
  }


  function addEmoji(emoji) {
    if (!emoji) return
    const separator = messageInput.value && !messageInput.value.endsWith(' ') ? ' ' : ''
    messageInput.value = `${messageInput.value || ''}${separator}${emoji} `
    showPicker.value = false
    emojiSearch.value = ''
    gifSearch.value = ''
    limitDraft()
  }

  function insertGif(gif) {
    if (!gif?.url) return
    const base = messageInput.value ? `${messageInput.value.trim()} ` : ''
    messageInput.value = `${base}${gif.url} `
    showPicker.value = false
    gifSearch.value = ''
    gifError.value = ''
    limitDraft()
  }




  function scrollToMessage(messageId) {

    const el = document.getElementById(`message-${messageId}`)

    if (el) {

      el.scrollIntoView({ behavior: 'smooth', block: 'center' })

      el.classList.add('msg-bubble--focus')

      setTimeout(() => {

        el.classList.remove('msg-bubble--focus')

      }, 1200)

    }

  }



  function extractError(err, fallback) {
    if (!err) return fallback
    if (typeof err === 'string') return err
    const data = err.response?.data
    const detail =
      (typeof data?.detail === 'string' && data.detail) ||
      (Array.isArray(data?.detail) && data.detail.length && data.detail[0]) ||
      data?.message ||
      data?.error ||
      err.message
    if (typeof detail === 'string' && detail.trim()) return detail.trim()
    return fallback
  }



  function handleDocumentClick() {
    if (forwardPicker.open) {
      cancelForwardSelection()
      return
    }
    if (!reactionPickerFor.value && !messageMenuOpen.value) return
    closeTransientMenus()
  }



  function handleDocumentKeydown(event) {
    if (event.key !== 'Escape') return
    if (forwardPicker.open) {
      event.preventDefault()
      cancelForwardSelection()
      return
    }
    if (!reactionPickerFor.value && !messageMenuOpen.value) return
    event.preventDefault()
    closeTransientMenus()
  }




  onMounted(async () => {
    await loadConversations()
    if (typeof window !== 'undefined') {
      document.addEventListener('click', handleDocumentClick)
      document.addEventListener('keydown', handleDocumentKeydown)
      window.addEventListener('storage', handleBrowserPrefStorage)
      window.addEventListener('cova:browser-notifications', handleBrowserPrefBroadcast)
    }
    syncBrowserNotificationPreference()
  })



  onBeforeUnmount(() => {
    disconnectRealtime()
    clearNotificationTimers()
    if (typeof window !== 'undefined') {
      document.removeEventListener('click', handleDocumentClick)
      document.removeEventListener('keydown', handleDocumentKeydown)
      window.removeEventListener('storage', handleBrowserPrefStorage)
      window.removeEventListener('cova:browser-notifications', handleBrowserPrefBroadcast)
    }
  })
  return {
    activeFilterLabel,
    addEmoji,
    applyConversationPatch,
    applyLocalReadReceipt,
    applyMemberPayload,
    applyMessageUpdate,
    applyUnreadMeta,
    attachmentError,
    attachmentInput,
    authToken,
    browserNotificationsEnabled,
    cancelComposerContext,
    canManageConversation,
    canSend,
    clearPendingAttachments,
    closeConversationPanel,
    closeSearchPanel,
    closeTransientMenus,
    composerState,
    computeInitials,
    confirmDeleteMessage,
    connectionStatus,
    connectionStatusClass,
    connectionStatusLabel,
    connectRealtime,
    conversationError,
    conversationFilter,
    conversationFilters,
    conversationForm,
    extractError,
    filteredEmojiSections,
    formatAbsolute,
    formatFileSize,
    formatInviteStatus,
    formatListTime,
    formatTime,
    generateLocalId,
    gifError,
    gifLibrary,
    gifResults,
    gifSearch,
    gifSearchAvailable,
    deleteDialog,
    deleteDialogPreview,
    closeDeleteDialog,
    performDeleteMessage,
    downloadAttachment,
    goToNewConversation,
    handleBrowserPrefBroadcast,
    handleBrowserPrefStorage,
    handleDocumentClick,
    handleDocumentKeydown,
    handleIncomingRealtime,
    handlePinToggle,
    handleReactionSelection,
    hasAttachmentInProgress,
    hasComposerContext,
    headerParticipants,
    headerSubtitle,
    primaryParticipantPresence,
    memberPresence,
    memberPresenceText,
    incrementUnreadCounter,
    initializeMeta,
    insertGif,
    initiateForward,
    inviteBusy,
    inviteForm,
    inviteRevokeBusy,
    invites,
    isConversationOwner,
    isEditingMessage,
    isPinning,
    isReactionPending,
    jumpToSearchResult,
    leaveCurrentConversation,
    leavingConversation,
    limitDraft,
    loadConversationInvites,
    loadConversations,

    loadingConversations,
    loadingGifs,
    loadingInvites,
    loadingMessages,
    loadingOlderMessages,
    loadOlderMessages,
    loadMessages,
    loadUnreadSummary,
    mapAttachmentPayload,
    mapInvite,
    mapOptimisticAttachments,
    mapReferencePayload,
    markConversationAsRead,
    memberBusy,
    messageError,
    messageInput,
    messageMenuOpen,
    messagePreviewText,
    messages,
    messageScroller,
    messageSearch,
    messageSecurityLabel,
    messageSecurityTooltip,
    messageStatusClass,
    messageStatusDetail,
    messageStatusLabel,
    messageToasts,
    muteMember,
    normalizeConversation,
    normalizeMember,
    normalizeMessage,
    notificationPermissionRequestPending,
    notifyNewIncomingMessage,
    onAttachmentChange,
    onAvatarFailure,
    onThreadScroll,
    openConversationPanel,
    openToastConversation,
    optimisticMessageIds,
    pagination,
    paginationHeaderKeys,
    pendingAttachments,
    performMessageSearch,
    pickerMode,
    pinnedMessages,
    queueAttachment,
    queueToastNotification,
    reactionPalette,
    reactionPickerFor,
    forwardPicker,
    forwardPickerInput,
    forwardPickerTargets,
    readHeader,
    readyAttachments,
    removeAttachment,
    removeMember,
    removeMessageById,
    resetComposerState,
    resetSearchPanel,
    resolveOptimisticMessage,
    revokeInvite,
    roleLabel,
    route,
    router,
    saveConversationSettings,
    savingConversation,
    scrollToBottom,
    scrollToMessage,
    selectConversation,
    selectedConversation,
    selectedConversationId,
    sending,
    sendMessage,
    setPickerMode,
    showConversationPanel,
    showPicker,
    showSearchPanel,
    socketRef,
    sortedConversations,
    startEdit,
    startForward,
    startReply,
    cancelForwardSelection,
    confirmForwardTarget,
    submitInvite,
    submitMessageEdit,
    suppressAutoScroll,
    syncBrowserNotificationPreference,
    syncConversationFormFromSelected,
    toggleMessageMenu,
    togglePicker,
    togglePin,
    toggleReaction,
    toggleReactionPicker,
    toggleSearchPanel,
    triggerAttachmentPicker,
    unmuteMember,
    unreadSummary,
    updateMemberRole,
    updatePaginationFromHeaders,
    uploadAttachmentFile
  }

