// ===== Module Header =====
// Module: messages/useMessageToasts
// Role: Gestion des toasts (file d'attente, auto-dismiss) et navigation vers la conversation cible.
// Notes: stocke les timers dans une Map pour nettoyer a l'unmount.

import { nextTick, onBeforeUnmount, ref } from 'vue'

export function useMessageToasts({
  router,
  selectConversation,
  ensureMessageVisible,
  generateLocalId,
}) {
  // ---- File des toasts affiches + timers d'auto-fermeture ----
  const messageToasts = ref([])
  const toastTimers = new Map()

  // ---- Supprime un toast et nettoie son timer ----
  function dismissToast(id) {
    messageToasts.value = messageToasts.value.filter((toast) => toast.id !== id)
    if (toastTimers.has(id)) {
      clearTimeout(toastTimers.get(id))
      toastTimers.delete(id)
    }
  }

  // ---- Action principale sur un toast (ouvre conversation ou route cible) ----
  async function openToastConversation(toast) {
    if (toast?.targetRoute) {
      router.push(toast.targetRoute).catch(() => {})
      dismissToast(toast.id)
      return
    }
    if (!toast?.conversationId) return
    await selectConversation(toast.conversationId)
    dismissToast(toast.id)
    await nextTick()
    if (toast.messageId) {
      await ensureMessageVisible(toast.messageId)
    }
  }

  // ---- Ajout d'un toast (limite a 4) et planification d'auto-dismiss ----
  function queueToastNotification({ title, body, conversationId, messageId, targetRoute }) {
    const toast = {
      id: generateLocalId(),
      title: title || 'Nouveau message',
      body: body || '',
      conversationId,
      messageId,
      targetRoute: targetRoute || null,
      createdAt: new Date(),
    }
    messageToasts.value = [toast, ...messageToasts.value].slice(0, 4)
    if (toastTimers.has(toast.id)) {
      clearTimeout(toastTimers.get(toast.id))
    }
    toastTimers.set(
      toast.id,
      setTimeout(() => {
        dismissToast(toast.id)
      }, 7000),
    )
  }

  onBeforeUnmount(() => {
    toastTimers.forEach((timer) => clearTimeout(timer))
    toastTimers.clear()
  })

  return {
    messageToasts,
    queueToastNotification,
    dismissToast,
    openToastConversation,
  }
}
