// ===== Module Header =====
// Module: messages/useDeleteMessage
// Role: Encapsule la logique du dialogue de suppression (ouverture, confirmation, preview).
// Notes: manipule seulement des refs; l'appel API est delegue a deleteConversationMessage.

import { computed, reactive } from 'vue'
import { deleteConversationMessage } from '@/services/conversations'

export function useDeleteMessage({
  selectedConversationId,
  messagePreviewText,
  applyMessageUpdate,
  normalizeMessage,
  extractError,
}) {
  // ---- Etat du dialog de suppression ----
  const deleteDialog = reactive({
    visible: false,
    message: null,
    loading: false,
    error: '',
  })

  // ---- Apercu court du message cible (pour affichage) ----
  const deleteDialogPreview = computed(() =>
    deleteDialog.message ? messagePreviewText(deleteDialog.message) : '',
  )

  // ---- Ouvre la confirmation ----
  function confirmDeleteMessage(message) {
    if (!message || !selectedConversationId.value) return
    deleteDialog.message = message
    deleteDialog.error = ''
    deleteDialog.visible = true
  }

  // ---- Ferme la modal si pas en cours de suppression ----
  function closeDeleteDialog() {
    if (deleteDialog.loading) return
    deleteDialog.visible = false
    deleteDialog.message = null
    deleteDialog.error = ''
  }

  // ---- Appelle l'API pour supprimer puis rafraichit le store ----
  async function performDeleteMessage() {
    if (!deleteDialog.message || !selectedConversationId.value) return
    deleteDialog.loading = true
    deleteDialog.error = ''
    try {
      const data = await deleteConversationMessage(
        selectedConversationId.value,
        deleteDialog.message.id,
      )
      applyMessageUpdate(normalizeMessage(data))
      closeDeleteDialog()
    } catch (err) {
      deleteDialog.error = extractError(err, "Impossible de supprimer le message.")
    } finally {
      deleteDialog.loading = false
    }
  }

  return {
    deleteDialog,
    deleteDialogPreview,
    confirmDeleteMessage,
    closeDeleteDialog,
    performDeleteMessage,
  }
}
