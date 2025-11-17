import { nextTick, ref, watch } from 'vue'

export function useNotificationsManager({
  selectedConversationId,
  selectConversation,
  ensureMessageVisible,
  messagePreviewText,
  generateLocalId,
}) {
  const messageToasts = ref([])
  const toastTimers = new Map()
  const browserNotificationsEnabled = ref(readBrowserNotificationPreference())
  const notificationPermissionRequestPending = ref(false)

  function readBrowserNotificationPreference() {
    try {
      return localStorage.getItem('notif_browser') === '1'
    } catch {
      return false
    }
  }

  function syncBrowserNotificationPreference() {
    browserNotificationsEnabled.value = readBrowserNotificationPreference()
  }

  function handleBrowserPrefStorage(event) {
    if (event?.key === 'notif_browser') {
      syncBrowserNotificationPreference()
    }
  }

  function handleBrowserPrefBroadcast(event) {
    if (event?.detail && typeof event.detail.enabled === 'boolean') {
      browserNotificationsEnabled.value = event.detail.enabled
    }
  }

  function queueToastNotification({ title, body, conversationId, messageId }) {
    const toast = {
      id: generateLocalId(),
      title: title || 'Nouveau message',
      body: body || '',
      conversationId,
      messageId,
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

  function dismissToast(id) {
    messageToasts.value = messageToasts.value.filter((toast) => toast.id !== id)
    if (toastTimers.has(id)) {
      clearTimeout(toastTimers.get(id))
      toastTimers.delete(id)
    }
  }

  async function openToastConversation(toast) {
    if (!toast?.conversationId) return
    await selectConversation(toast.conversationId)
    dismissToast(toast.id)
    await nextTick()
    if (toast.messageId) {
      await ensureMessageVisible(toast.messageId)
    }
  }

  function notifyNewIncomingMessage(message) {
    if (!message || message.sentByMe || message.deleted || message.isSystem) return
    const preview =
      message.preview ||
      messagePreviewText(message) ||
      (message.content ? String(message.content).slice(0, 140) : 'Nouveau message securise.')
    const shouldToast = message.conversationId !== selectedConversationId.value
    const browserAllowed =
      browserNotificationsEnabled.value &&
      typeof Notification !== 'undefined' &&
      Notification.permission === 'granted'
    const docHidden =
      typeof document !== 'undefined' && (document.hidden || !document.hasFocus())
    if (shouldToast) {
      queueToastNotification({
        title: message.displayName || 'Nouveau message',
        body: preview,
        conversationId: message.conversationId,
        messageId: message.id,
      })
    }
    const shouldBrowser = browserAllowed && (docHidden || shouldToast)
    if (shouldBrowser) {
      triggerBrowserNotification(message, preview)
    }
  }

  function triggerBrowserNotification(message, body) {
    if (!browserNotificationsEnabled.value || typeof Notification === 'undefined') return
    if (Notification.permission === 'granted') {
      const notification = new Notification(message.displayName || 'Messagerie securisee', {
        body,
        tag: message.conversationId,
      })
      notification.onclick = () => {
        window.focus()
        openToastConversation({
          conversationId: message.conversationId,
          id: message.id,
          messageId: message.id,
        })
        notification.close()
      }
      return
    }
    if (Notification.permission === 'default' && !notificationPermissionRequestPending.value) {
      notificationPermissionRequestPending.value = true
      Notification.requestPermission()
        .catch(() => {})
        .finally(() => {
          notificationPermissionRequestPending.value = false
        })
    }
  }

  function clearNotificationTimers() {
    toastTimers.forEach((timer) => clearTimeout(timer))
    toastTimers.clear()
  }

  watch(
    browserNotificationsEnabled,
    (enabled) => {
      if (
        enabled &&
        typeof Notification !== 'undefined' &&
        Notification.permission === 'default' &&
        !notificationPermissionRequestPending.value
      ) {
        notificationPermissionRequestPending.value = true
        Notification.requestPermission()
          .catch(() => {})
          .finally(() => {
            notificationPermissionRequestPending.value = false
          })
      }
    },
    { immediate: true },
  )

  return {
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
  }
}
