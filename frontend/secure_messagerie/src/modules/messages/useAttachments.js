// ===== Module Header =====
// Module: messages/useAttachments
// Role: Piloter la selection et l'upload des pieces jointes du composeur (queue + erreurs).
// Usage: manipule des refs externes (pendingAttachments, attachmentError) et des callbacks fournis par le caller.
// Notes: aucune dependance UI (DOM uniquement pour trouver l'input file si non fourni).

import { reactive } from 'vue'

export function useAttachments({
  selectedConversationId,
  pendingAttachments,
  attachmentError,
  attachmentInput,
  uploadAttachment,
  extractError,
}) {
  // ---- Ouvre le picker et valide qu'une conversation est ciblee ----
  function triggerAttachmentPicker() {
    attachmentError.value = ''
    if (!selectedConversationId.value) {
      attachmentError.value = 'Sélectionnez une conversation avant d\'ajouter un fichier.'
      return
    }
    const inputEl =
      attachmentInput?.value ||
      (typeof document !== 'undefined'
        ? document.querySelector('.msg-composer input[type="file"]')
        : null)
    if (!inputEl) {
      attachmentError.value = 'Sélecteur de fichiers indisponible. Rechargez la page.'
      return
    }
    inputEl.value = ''
    inputEl.click()
  }

  // ---- Convertit l'evenement file en queue d'upload ----
  function onAttachmentChange(event) {
    const files = Array.from(event.target?.files || [])
    if (!files.length) return
    files.forEach((file) => queueAttachment(file))
  }

  // ---- Ajoute un fichier dans pendingAttachments puis lance l'upload ----
  function queueAttachment(file) {
    if (!file) return
    const entry = reactive({
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      name: file.name,
      size: file.size,
      type: file.type,
      file,
      status: 'uploading',
      progress: 0,
      descriptor: null,
      error: '',
    })
    pendingAttachments.value = [...pendingAttachments.value, entry]
    uploadAttachmentFile(entry)
  }

  // ---- Upload vers l'API et mise a jour de la progression/erreur ----
  async function uploadAttachmentFile(entry) {
    if (!selectedConversationId.value) {
      entry.status = 'error'
      entry.error = 'Aucune conversation active.'
      return
    }
    attachmentError.value = ''
    try {
      const descriptor = await uploadAttachment(selectedConversationId.value, entry.file, {
        onUploadProgress: (event) => {
          if (!event || !event.total) return
          entry.progress = Math.min(100, Math.round((event.loaded / event.total) * 100))
        },
      })
      entry.descriptor = descriptor
      entry.status = 'ready'
      entry.progress = 100
    } catch (err) {
      entry.status = 'error'
      entry.error = extractError(err, 'Impossible de téléverser le fichier.')
      attachmentError.value = entry.error
    }
  }

  // ---- Retrait d'un fichier en attente ----
  function removeAttachment(entryId) {
    pendingAttachments.value = pendingAttachments.value.filter((item) => item.id !== entryId)
  }

  // ---- Nettoyage complet des fichiers en attente et des erreurs ----
  function clearPendingAttachments() {
    pendingAttachments.value = []
    attachmentError.value = ''
  }

  return {
    triggerAttachmentPicker,
    onAttachmentChange,
    queueAttachment,
    uploadAttachmentFile,
    removeAttachment,
    clearPendingAttachments,
  }
}
