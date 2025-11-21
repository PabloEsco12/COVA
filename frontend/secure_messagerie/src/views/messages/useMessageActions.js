import { reactive, ref } from 'vue'
import { pinMessage, unpinMessage, updateMessageReaction } from '@/services/conversations'
import { createMessageFormatters } from '@/views/messages/message-formatters'

export function useMessageActions({
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
}) {
  const pinBusy = reactive({})
  const reactionBusy = reactive({})
  const reactionPickerFor = ref(null)
  const messageMenuOpen = ref(null)
  const copiedMessageId = ref(null)
  const optimisticMessageIds = new Set()
  let copyTimer = null

  function cloneComposerReference(target) {
    if (!target) return null
    return {
      id: target.id,
      displayName: target.displayName,
      authorDisplayName: target.authorDisplayName || target.displayName || target.email || 'Participant',
      excerpt: target.excerpt || messagePreviewText(target),
      deleted: Boolean(target.deleted),
    }
  }

  function mapOptimisticAttachments(entries) {
    return entries.map((entry) => ({
      id: entry.descriptor?.id || entry.id,
      fileName: entry.name || entry.descriptor?.file_name || 'Pièce jointe',
      mimeType: entry.type || entry.descriptor?.mime_type || 'Fichier',
      sizeBytes: entry.size,
      downloadUrl: entry.descriptor?.download_url || null,
    }))
  }

  function removeMessageById(messageId) {
    const idx = messages.value.findIndex((msg) => msg.id === messageId)
    if (idx !== -1) {
      messages.value.splice(idx, 1)
    }
  }

  function resolveOptimisticMessage(localId, nextMessage) {
    optimisticMessageIds.delete(localId)
    removeMessageById(localId)
    applyMessageUpdate(nextMessage)
  }

  function isPinning(messageId) {
    return Boolean(pinBusy[messageId])
  }

  function isReactionPending(messageId, emoji) {
    return Boolean(reactionBusy[`${messageId}:${emoji}`])
  }

  function toggleReactionPicker(messageId) {
    if (!messageId) return
    reactionPickerFor.value = reactionPickerFor.value === messageId ? null : messageId
    if (reactionPickerFor.value) {
      messageMenuOpen.value = null
    }
  }

  function toggleMessageMenu(messageId) {
    if (!messageId) return
    messageMenuOpen.value = messageMenuOpen.value === messageId ? null : messageId
    if (messageMenuOpen.value) {
      reactionPickerFor.value = null
    }
  }

  function closeTransientMenus() {
    reactionPickerFor.value = null
    messageMenuOpen.value = null
  }

  async function handlePinToggle(message) {
    await togglePin(message)
    closeTransientMenus()
  }

  async function handleReactionSelection(message, emoji) {
    await toggleReaction(message, emoji)
    reactionPickerFor.value = null
  }

  async function togglePin(message) {
    if (!selectedConversationId.value) return
    const messageId = message.id
    pinBusy[messageId] = true
    try {
      const data = message.pinned
        ? await unpinMessage(selectedConversationId.value, messageId)
        : await pinMessage(selectedConversationId.value, messageId)
      applyMessageUpdate(normalizeMessage(data, { selfId: currentUserId.value }))
    } catch (err) {
      messageError.value = extractError(err, "Impossible de mettre à jour l'épingle.")
    } finally {
      pinBusy[messageId] = false
    }
  }

  async function toggleReaction(message, emoji) {
    if (!selectedConversationId.value || !emoji) return
    const key = `${message.id}:${emoji}`
    reactionBusy[key] = true
    try {
      const data = await updateMessageReaction(selectedConversationId.value, message.id, { emoji })
      applyMessageUpdate(normalizeMessage(data, { selfId: currentUserId.value }))
    } catch (err) {
      console.warn('Impossible de mettre à jour la réaction', err)
    } finally {
      reactionBusy[key] = false
    }
  }

  async function copyMessage(message) {
    if (!message?.content) return
    try {
      if (navigator?.clipboard?.writeText) {
        await navigator.clipboard.writeText(message.content)
        copiedMessageId.value = message.id
        if (copyTimer) clearTimeout(copyTimer)
        copyTimer = setTimeout(() => {
          copiedMessageId.value = null
          copyTimer = null
        }, 1500)
      }
    } catch (err) {
      console.warn('Impossible de copier le message', err)
    }
  }

  function downloadAttachment(attachment) {
    if (!attachment || !attachment.downloadUrl) return
    window.open(attachment.downloadUrl, '_blank', 'noopener')
  }

  const messageFormatters = createMessageFormatters({
    formatTime,
    formatAbsolute,
    formatFileSize,
    extractDeliverySummary,
  })

  return {
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
  }
}
