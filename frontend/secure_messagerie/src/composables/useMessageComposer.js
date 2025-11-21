import { computed, nextTick, reactive, ref } from 'vue'
import { api } from '@/utils/api'
import { mapOptimisticAttachments } from '@/utils/messageContent'

export function useMessageComposer({
  onSendSuccess,
  onSendError,
  onAfterSend,
  formatFileSize,
  scrollToBottom,
}) {
  const messageInput = ref('')
  const sending = ref(false)
  const attachmentError = ref('')
  const pendingAttachments = ref([])
  const readyAttachments = ref([])
  const attachmentInput = ref(null)

  const composerState = reactive({
    mode: 'new',
    targetMessageId: null,
    replyTo: null,
    forwardFrom: null,
  })

  const isEditingMessage = computed(
    () => composerState.mode === 'edit' && Boolean(composerState.targetMessageId),
  )
  const hasComposerContext = computed(() => {
    return (
      composerState.replyTo !== null ||
      composerState.forwardFrom !== null ||
      composerState.mode === 'edit'
    )
  })

  const readyAttachmentList = computed(() =>
    pendingAttachments.value.filter((entry) => entry.status === 'ready'),
  )

  const hasAttachmentInProgress = computed(() =>
    pendingAttachments.value.some((entry) => entry.status === 'uploading'),
  )

  function resetComposerState() {
    composerState.mode = 'new'
    composerState.targetMessageId = null
    composerState.replyTo = null
    composerState.forwardFrom = null
  }

  function cancelComposerContext() {
    resetComposerState()
  }

  function handleComposerBlur() {
    /* hook utilisé côté vue pour stopper le typing */
  }

  function onComposerInput() {
    /* hook utilisé côté vue pour le typing */
  }

  function triggerAttachmentPicker() {
    attachmentError.value = ''
    if (attachmentInput.value) {
      attachmentInput.value.value = ''
      attachmentInput.value.click()
    }
  }

  function startReply(message) {
    if (!message) return
    composerState.mode = 'reply'
    composerState.replyTo = message
    composerState.forwardFrom = null
    composerState.targetMessageId = null
  }

  function startForward(message) {
    if (!message) return
    composerState.mode = 'forward'
    composerState.forwardFrom = message
    composerState.replyTo = null
    composerState.targetMessageId = null
    if (!messageInput.value) {
      messageInput.value = message.content || ''
    }
  }

  function startEdit(message) {
    if (!message) return
    composerState.mode = 'edit'
    composerState.targetMessageId = message.id
    composerState.replyTo = null
    composerState.forwardFrom = null
    messageInput.value = message.content || ''
  }

  function onAttachmentChange(event) {
    const files = Array.from(event?.target?.files || [])
    if (!files.length) return
    const mapped = files.map((file) => ({
      id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      descriptor: { file_name: file.name, file_size: file.size },
      status: 'ready',
      progress: 0,
      file,
      name: file.name,
      size: file.size,
    }))
    pendingAttachments.value = [...pendingAttachments.value, ...mapped]
  }

  function removeAttachment(id) {
    pendingAttachments.value = pendingAttachments.value.filter((item) => item.id !== id)
    readyAttachments.value = readyAttachments.value.filter((item) => item.id !== id)
  }

  const pickerMode = ref('emoji')
  const showPicker = ref(false)
  const emojiSearch = ref('')
  const gifSearch = ref('')

  async function sendMessage({
    selectedConversationId,
    composerStateSnapshot,
    attachmentsPayload,
    payload,
    normalizeMessage,
    optimisticMessages,
    optimisticMessageIds,
    readyAttachmentsSnapshot,
    stopTyping,
  }) {
    if (!selectedConversationId) return
    if (sending.value) return
    const draftContent = messageInput.value.trim()
    if (!draftContent && !attachmentsPayload.length) return
    if (hasAttachmentInProgress.value) {
      attachmentError.value = 'Sélectionnez une conversation avant d\'ajouter un fichier.'
      return
    }
    sending.value = true
    const optimisticId = `msg_${Math.random().toString(36).slice(2, 10)}`
    const optimisticMessage = {
      id: optimisticId,
      conversationId: selectedConversationId,
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
      attachments: mapOptimisticAttachments(readyAttachmentsSnapshot),
      replyTo: composerStateSnapshot.replyTo,
      forwardFrom: composerStateSnapshot.forwardFrom,
      localOnly: true,
    }
    optimisticMessages.push(optimisticMessage)
    optimisticMessageIds.add(optimisticId)
    const previousInputValue = messageInput.value
    messageInput.value = ''
    await nextTick()
    scrollToBottom?.()
    try {
      const { data } = await api.post(`/conversations/${selectedConversationId}/messages`, payload)
      const message = normalizeMessage(data)
      message.sentByMe = true
      onSendSuccess?.(optimisticId, message)
      showPicker.value = false
      emojiSearch.value = ''
      gifSearch.value = ''
      attachmentError.value = ''
      if (typeof stopTyping === 'function') stopTyping()
    } catch (err) {
      onSendError?.(optimisticId, err)
      messageInput.value = previousInputValue
    } finally {
      sending.value = false
      onAfterSend?.()
    }
  }

  return {
    messageInput,
    sending,
    attachmentError,
    pendingAttachments,
    readyAttachments: readyAttachmentList,
    hasAttachmentInProgress,
    attachmentInput,
    composerState,
    isEditingMessage,
    hasComposerContext,
    cancelComposerContext,
    handleComposerBlur,
    onComposerInput,
    triggerAttachmentPicker,
    resetComposerState,
    startReply,
    startForward,
    startEdit,
    onAttachmentChange,
    removeAttachment,
    pickerMode,
    showPicker,
    emojiSearch,
    gifSearch,
    sendMessage,
  }
}
