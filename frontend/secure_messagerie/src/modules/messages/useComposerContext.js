// ===== Module Header =====
// Module: messages/useComposerContext
// Role: Gere les modes du composeur (repondre/transfert/edition) et navigation cible.
// Notes: manipule des refs externes (composerState, forwardPicker) sans toucher a l'API d'envoi.

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
  // ---- Passe le composeur en mode reponse ----
  function startReply(message) {
    if (!message) return
    composerState.mode = 'reply'
    composerState.replyTo = message
    composerState.forwardFrom = null
    composerState.targetMessageId = null
  }

  // ---- Passe le composeur en mode transfert (copie le contenu si besoin) ----
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

  // ---- Passe le composeur en mode edition d'un message existant ----
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

  // ---- Ouvre la modale de choix de conversation pour le transfert ----
  function initiateForward(message) {
    if (!message) return
    forwardPicker.open = true
    forwardPicker.message = message
    forwardPicker.query = ''
  }

  // ---- Ferme la selection de transfert ----
  function cancelForwardSelection() {
    forwardPicker.open = false
    forwardPicker.message = null
    forwardPicker.query = ''
  }

  // ---- Confirme la conversation cible pour un transfert et bascule si besoin ----
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
