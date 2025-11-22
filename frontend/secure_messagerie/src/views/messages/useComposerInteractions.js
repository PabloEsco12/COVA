import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { api } from '@/utils/api'
import { editConversationMessage } from '@/services/conversations'
import { fetchGifs, hasGifApiSupport } from '@/services/media'
import { emojiCatalog, emojiSections, defaultGifLibrary } from '@/utils/reactions'

export function useComposerInteractions({
  messageInput,
  composerState,
  showPicker,
  pickerMode,
  emojiSearch,
  gifSearch,
  pendingAttachments,
  readyAttachments,
  hasAttachmentInProgress,
  isEditingMessage,
  selectedConversation,
  selectedConversationId,
  currentUserId,
  attachmentError,
  messages,
  messageError,
  mapOptimisticAttachments,
  cloneComposerReference,
  resolveOptimisticMessage,
  optimisticMessageIds,
  removeMessageById,
  clearPendingAttachments,
  resetComposerState,
  ensureMeta,
  loadUnreadSummary,
  normalizeMessage,
  extractError,
  updateConversationBlockStateByUser,
  memberUserId,
  applyMessageUpdate,
  scrollToBottom,
  socketRef,
  generateLocalId,
  sending,
}) {
  const gifLibrary = defaultGifLibrary
  const gifResults = ref(gifLibrary.slice())
  const loadingGifs = ref(false)
  const gifError = ref('')
  const gifSearchAvailable = hasGifApiSupport()
  const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
  const localTypingState = reactive({ active: false, timer: null })
  const LOCAL_TYPING_IDLE_MS = 3500
  let gifSearchTimer = null

  function isValidUuid(value) {
    return typeof value === 'string' && UUID_PATTERN.test(value)
  }

  const filteredEmojiSections = computed(() => {
    const term = emojiSearch.value.trim().toLowerCase()
    if (!term) return emojiSections
    const matches = emojiSections
      .map((section) => ({
        ...section,
        items: section.items.filter((emoji) => emoji.toLowerCase().includes(term)),
      }))
      .filter((section) => section.items.length)
    if (matches.length) return matches
    return [
      {
        id: 'search',
        label: 'RǸsultats',
        items: emojiCatalog.filter((emoji) => emoji.toLowerCase().includes(term)),
      },
    ]
  })

  const displayedGifs = computed(() => (gifResults.value.length ? gifResults.value : gifLibrary))

  const composerBlockedInfo = computed(() => {
    const conv = selectedConversation.value
    if (!conv) return null
    if (conv.blockedByOther) {
      return {
        state: 'blocked_by_other',
        title: 'Conversation bloqu�e par le contact',
        message:
          `${conv.displayName || 'Ce contact'} a bloqu� cette conversation. Vous ne pouvez plus r�pondre tant que le contact ne vous a pas d�bloqu�.`,
      }
    }
    if (conv.blockedByMe) {
      return {
        state: 'blocked_by_me',
        title: 'Vous avez bloquǸ ce contact',
        message: `DǸbloquez ${conv.displayName || 'ce contact'} depuis la section Contacts pour reprendre l�?TǸchange.`,
      }
    }
    return null
  })
  const isComposerBlocked = computed(() => Boolean(composerBlockedInfo.value))

  const canSend = computed(() => {
    if (isComposerBlocked.value) return false
    const value = messageInput.value.trim()
    const attachmentsReady = readyAttachments.value.length > 0 && !isEditingMessage.value
    return (
      (Boolean(value) ||
        attachmentsReady ||
        composerState.mode === 'reply' ||
        composerState.mode === 'forward') &&
      value.length <= 2000 &&
      Boolean(selectedConversationId.value)
    )
  })

  watch([showPicker, pickerMode], ([visible, mode]) => {
    if (visible && mode === 'gif') {
      loadGifResults(gifSearch.value)
    }
  })

  watch(gifSearch, (term) => {
    if (pickerMode.value !== 'gif' || !showPicker.value) return
    if (gifSearchTimer) clearTimeout(gifSearchTimer)
    gifSearchTimer = setTimeout(() => {
      loadGifResults(term)
    }, 350)
  })

  watch(
    () => composerBlockedInfo.value?.state,
    (state, previous) => {
      if (state && state !== previous) {
        messageInput.value = ''
        clearPendingAttachments()
        resetComposerState()
      }
    },
  )

async function loadGifResults(query = '') {
  if (!showPicker.value || pickerMode.value !== 'gif') {
    return
  }
    if (!gifSearchAvailable) {
      gifResults.value = gifLibrary
      gifError.value = ''
      return
    }
    loadingGifs.value = true
    gifError.value = ''
    try {
      const gifs = await fetchGifs({ query, limit: 30 })
      gifResults.value = gifs.length ? gifs : gifLibrary
    } catch (error) {
      gifResults.value = gifLibrary
      gifError.value = "Impossible de charger les GIFs."
    } finally {
    loadingGifs.value = false
  }
}

function resetPickerState() {
  showPicker.value = false
  pickerMode.value = 'emoji'
  emojiSearch.value = ''
  gifSearch.value = ''
  gifError.value = ''
  loadingGifs.value = false
  gifResults.value = gifLibrary.slice()
}

function togglePicker() {
  showPicker.value = !showPicker.value
  if (showPicker.value) {
    pickerMode.value = 'emoji'
    emojiSearch.value = ''
    gifSearch.value = ''
    gifError.value = ''
  } else {
    resetPickerState()
  }
}

  function setPickerMode(mode) {
    pickerMode.value = mode
    showPicker.value = true
    if (mode !== 'emoji') {
      emojiSearch.value = ''
    }
    if (mode === 'gif') {
      loadGifResults(gifSearch.value)
    }
  }

  function limitDraft() {
    if (messageInput.value.length > 2000) {
      messageInput.value = messageInput.value.slice(0, 2000)
    }
  }

  function handleTypingActivity() {
    if (!selectedConversationId.value || !socketRef.value) {
      stopLocalTyping()
      return
    }
    if (!messageInput.value.trim()) {
      stopLocalTyping()
      return
    }
    if (!localTypingState.active) {
      try {
        socketRef.value.send({ event: 'typing:start' })
      } catch {}
      localTypingState.active = true
    }
    if (localTypingState.timer) {
      clearTimeout(localTypingState.timer)
    }
    localTypingState.timer = setTimeout(() => stopLocalTyping(), LOCAL_TYPING_IDLE_MS)
  }

  function handleComposerBlur() {
    stopLocalTyping()
  }

  function stopLocalTyping() {
    if (localTypingState.timer) {
      clearTimeout(localTypingState.timer)
      localTypingState.timer = null
    }
    if (!localTypingState.active || !socketRef.value) {
      localTypingState.active = false
      return
    }
    try {
      socketRef.value.send({ event: 'typing:stop' })
    } catch {}
    localTypingState.active = false
  }

  function onComposerInput() {
    limitDraft()
    handleTypingActivity()
  }

  function addEmoji(emoji) {
    if (!emoji) return
    const separator = messageInput.value && !messageInput.value.endsWith(' ') ? ' ' : ''
    messageInput.value = `${messageInput.value || ''}${separator}${emoji} `
    showPicker.value = false
    emojiSearch.value = ''
    gifSearch.value = ''
    limitDraft()
    handleTypingActivity()
  }

  function insertGif(gif) {
    if (!gif?.url) return
    const base = messageInput.value ? `${messageInput.value.trim()} ` : ''
    messageInput.value = `${base}${gif.url} `
    showPicker.value = false
    gifSearch.value = ''
    gifError.value = ''
    limitDraft()
    handleTypingActivity()
  }

  function applyConversationBlockDetail(detail) {
    const conv = selectedConversation.value
    if (!conv || conv.type !== 'direct' || !Array.isArray(conv.members)) return
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    const other = conv.members.find((member) => memberUserId(member) !== selfId)
    const otherUserId = memberUserId(other)
    if (!other || !otherUserId) return
    updateConversationBlockStateByUser(otherUserId, {
      blockedByOther:
        Object.prototype.hasOwnProperty.call(detail || {}, 'blocked_by_other') && detail
          ? Boolean(detail.blocked_by_other)
          : undefined,
      blockedByMe:
        Object.prototype.hasOwnProperty.call(detail || {}, 'blocked_by_you') && detail
          ? Boolean(detail.blocked_by_you)
          : undefined,
    })
  }

  async function sendMessage() {
    if (!selectedConversationId.value || !canSend.value) return
    if (composerState.mode === 'edit' && composerState.targetMessageId) {
      await submitMessageEdit()
      return
    }
    if (hasAttachmentInProgress.value) {
      attachmentError.value = 'SǸlectionnez une conversation avant d\'ajouter un fichier.'
      return
    }
    if (pendingAttachments.value.some((entry) => entry.status === 'error')) {
      attachmentError.value = 'Retirez ou renvoyez les fichiers en erreur avant l\'envoi.'
      return
    }
    attachmentError.value = ''
    const readyList = pendingAttachments.value.filter((entry) => entry.status === 'ready')
    const attachmentsPayload = readyList
      .map((entry) => entry.descriptor?.upload_token)
      .filter(Boolean)
      .map((token) => ({ upload_token: token }))
    const draftContent = messageInput.value.trim()
    const forwardSameConversation =
      composerState.forwardFrom &&
      composerState.forwardFrom.conversationId &&
      selectedConversationId.value &&
      String(composerState.forwardFrom.conversationId) === String(selectedConversationId.value)
    const replyToId =
      composerState.replyTo && isValidUuid(composerState.replyTo.id) ? composerState.replyTo.id : null
    const forwardId =
      composerState.forwardFrom &&
      forwardSameConversation &&
      isValidUuid(composerState.forwardFrom.id)
        ? composerState.forwardFrom.id
        : null
    const payload = {
      content: draftContent,
      attachments: attachmentsPayload,
      reply_to_message_id: replyToId,
      forward_message_id: forwardId,
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
      attachments: mapOptimisticAttachments(readyList),
      replyTo: cloneComposerReference(composerState.replyTo),
      forwardFrom: forwardSameConversation ? cloneComposerReference(composerState.forwardFrom) : null,
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
    const { data } = await api.post(
      `/conversations/${selectedConversationId.value}/messages`,
      payload,
    )
    const message = normalizeMessage(data, { selfId: currentUserId.value })
    message.sentByMe = true
    resolveOptimisticMessage(optimisticId, message)
    resetPickerState()
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
      const detail = err?.response?.data?.detail || err?.response?.data
      if (detail && typeof detail === 'object' && detail.code === 'conversation_blocked') {
        applyConversationBlockDetail(detail)
        messageError.value =
          detail.reason === 'blocked_by_other'
            ? 'Ce contact a bloquǸ cette conversation.'
            : 'Vous avez bloquǸ cette conversation.'
      } else {
        messageError.value = extractError(err, "Impossible d'envoyer le message.")
      }
    } finally {
      sending.value = false
      stopLocalTyping()
    }
  }

  async function submitMessageEdit() {
    if (
      !selectedConversationId.value ||
      !composerState.targetMessageId ||
      !isValidUuid(composerState.targetMessageId)
    ) {
      return
    }
    sending.value = true
    try {
      const data = await editConversationMessage(selectedConversationId.value, composerState.targetMessageId, {
        content: messageInput.value.trim(),
      })
      const message = normalizeMessage(data, { selfId: currentUserId.value })
      message.sentByMe = true
      applyMessageUpdate(message)
      messageInput.value = ''
      resetComposerState()
      showPicker.value = false
    } catch (err) {
      messageError.value = extractError(err, 'Impossible de modifier le message.')
    } finally {
      sending.value = false
      stopLocalTyping()
    }
  }

  onBeforeUnmount(() => {
    stopLocalTyping()
    if (gifSearchTimer) {
      clearTimeout(gifSearchTimer)
      gifSearchTimer = null
    }
  })

  return {
    filteredEmojiSections,
    displayedGifs,
    gifError,
    loadingGifs,
    gifSearchAvailable,
    composerBlockedInfo,
    isComposerBlocked,
    canSend,
    togglePicker,
  setPickerMode,
  resetPickerState,
  addEmoji,
  insertGif,
  onComposerInput,
  handleComposerBlur,
  stopLocalTyping,
    sendMessage,
    submitMessageEdit,
  }
}
