export function useComposerContext({
  composerState,
  messageInput,
  clearPendingAttachments,
  selectedConversationId,
  selectConversation,
  route,
  router,
  messageError,
  forwardPicker,
  resetComposerState,
}) {
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
    clearPendingAttachments()
  }

  function cancelComposerContext() {
    resetComposerState()
  }

  function initiateForward(message) {
    if (!message) return
    forwardPicker.open = true
    forwardPicker.message = message
    forwardPicker.query = ''
  }

  function cancelForwardSelection() {
    forwardPicker.open = false
    forwardPicker.message = null
    forwardPicker.query = ''
  }

  async function confirmForwardTarget(conversationId) {
    if (!forwardPicker.message) {
      cancelForwardSelection()
      return
    }
    const targetMessage = forwardPicker.message
    let targetSelected = true
    cancelForwardSelection()
    const normalizedId = conversationId ? String(conversationId) : null
    if (normalizedId && normalizedId !== selectedConversationId.value) {
      try {
        await selectConversation(normalizedId)
      } catch (error) {
        targetSelected = false
        messageError.value = "Impossible d'ouvrir la conversation cible pour le transfert."
        console.warn("Impossible d'ouvrir la conversation cible pour le transfert.", error)
      }
    }
    if (targetSelected && normalizedId && normalizedId !== selectedConversationId.value) {
      if (String(selectedConversationId.value) !== normalizedId) return
    }
    if (targetSelected) {
      startForward(targetMessage)
    }
  }

  return {
    startReply,
    startForward,
    startEdit,
    cancelComposerContext,
    initiateForward,
    cancelForwardSelection,
    confirmForwardTarget,
  }
}
