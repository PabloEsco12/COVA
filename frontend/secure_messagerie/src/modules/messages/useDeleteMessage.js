import { computed, reactive } from 'vue'
import { deleteConversationMessage } from '@/services/conversations'

export function useDeleteMessage({
  selectedConversationId,
  messagePreviewText,
  applyMessageUpdate,
  normalizeMessage,
  extractError,
}) {
  const deleteDialog = reactive({
    visible: false,
    message: null,
    loading: false,
    error: '',
  })

  const deleteDialogPreview = computed(() =>
    deleteDialog.message ? messagePreviewText(deleteDialog.message) : '',
  )

  function confirmDeleteMessage(message) {
    if (!message || !selectedConversationId.value) return
    deleteDialog.message = message
    deleteDialog.error = ''
    deleteDialog.visible = true
  }

  function closeDeleteDialog() {
    if (deleteDialog.loading) return
    deleteDialog.visible = false
    deleteDialog.message = null
    deleteDialog.error = ''
  }

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
