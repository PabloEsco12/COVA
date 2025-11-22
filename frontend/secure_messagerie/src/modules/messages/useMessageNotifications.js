import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

function readBrowserNotificationPreference() {
  try {
    return localStorage.getItem('notif_browser') === '1'
  } catch {
    return false
  }
}

export function useMessageNotifications({
  selectedConversationId,
  currentUserId,
  queueToastNotification,
  openToastConversation,
  setUnreadForConversation,
  ensureMeta,
  updateConversationBlockStateByUser,
  generateLocalId,
}) {
  const browserNotificationsEnabled = ref(readBrowserNotificationPreference())
  let notificationPermissionRequestPending = false

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

  function triggerBrowserNotification(message, body) {
    if (typeof window !== 'undefined' && window.__covaGlobalBrowserNotifications) return
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
    if (Notification.permission === 'default' && !notificationPermissionRequestPending) {
      notificationPermissionRequestPending = true
      Notification.requestPermission()
        .catch(() => {})
        .finally(() => {
          notificationPermissionRequestPending = false
        })
    }
  }

  function triggerBrowserNotificationFromEvent(meta) {
    if (typeof window !== 'undefined' && window.__covaGlobalBrowserNotifications) return
    if (!browserNotificationsEnabled.value || typeof Notification === 'undefined') return
    if (Notification.permission !== 'granted') return
    const notification = new Notification(meta.title || 'Messagerie securisee', {
      body: meta.body || '',
      tag: meta.conversationId || meta.type || 'notification',
    })
    notification.onclick = () => {
      window.focus()
      openToastConversation({
        id: meta.messageId || generateLocalId(),
        conversationId: meta.conversationId,
        messageId: meta.messageId,
        targetRoute: meta.targetRoute,
      })
      notification.close()
    }
  }

  function notifyPendingContactsRefresh() {
    if (typeof window === 'undefined') return
    window.dispatchEvent(new CustomEvent('cova:contacts-pending', { detail: { refresh: true } }))
  }

  function handleContactNotificationEvent(event) {
    const title = event.title || 'Notification de contact'
    const body = event.body || 'Une mise a jour de vos contacts est disponible.'
    queueToastNotification({
      title,
      body,
      targetRoute: '/dashboard/contacts',
    })
    triggerBrowserNotificationFromEvent({
      title,
      body,
      targetRoute: '/dashboard/contacts',
    })
    notifyPendingContactsRefresh()
  }

  function handleContactBlockEvent(event) {
    const isUnblocked = event.type === 'contact.unblocked'
    const flagValue = !isUnblocked
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    let otherId = null
    const updates = {}
    if (event.blocked_by || event.unblocked_by) {
      const candidate = String(event.blocked_by || event.unblocked_by)
      if (!selfId || candidate !== selfId) {
        otherId = candidate
        updates.blockedByOther = flagValue
      }
    }
    if (event.blocked_target || event.unblocked_target) {
      const candidate = String(event.blocked_target || event.unblocked_target)
      otherId = candidate
      updates.blockedByMe = flagValue
    }
    if (otherId) {
      updateConversationBlockStateByUser(otherId, updates)
    }
    const title = event.title || (isUnblocked ? 'Contact debloque' : 'Contact bloque')
    const body =
      event.body ||
      (isUnblocked ? 'La conversation a ete reactivee.' : 'La conversation est bloquee jusqu a nouvel ordre.')
    queueToastNotification({
      title,
      body,
      targetRoute: '/dashboard/contacts',
    })
    triggerBrowserNotificationFromEvent({
      title,
      body,
      targetRoute: '/dashboard/contacts',
    })
    notifyPendingContactsRefresh()
  }

  function notifyNewIncomingMessage(message) {
    if (!message || message.sentByMe || message.deleted || message.isSystem) return
    const preview =
      message.preview ||
      (message.content ? String(message.content).slice(0, 140) : 'Nouveau message securise.')
    const shouldToast = message.conversationId !== selectedConversationId.value
    const browserAllowed =
      browserNotificationsEnabled.value && typeof Notification !== 'undefined' && Notification.permission === 'granted'
    const docHidden = typeof document !== 'undefined' && (document.hidden || !document.hasFocus())
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

  function handleMessageNotificationEvent(event) {
    if (event?.author_id && currentUserId.value && String(event.author_id) === String(currentUserId.value)) {
      return
    }
    const conversationId = event.conversation_id ? String(event.conversation_id) : null
    if (!conversationId || conversationId === String(selectedConversationId.value)) return
    const meta = ensureMeta(conversationId)
    if (event.preview) meta.lastPreview = event.preview
    meta.lastActivity = event.created_at ? new Date(event.created_at) : new Date()
    meta.unreadCount = (meta.unreadCount || 0) + 1
    setUnreadForConversation(conversationId, meta.unreadCount)
    const title = event.sender || 'Nouveau message'
    const body = event.preview || 'Message securise'
    queueToastNotification({
      title,
      body,
      conversationId,
      messageId: event.message_id,
    })
    triggerBrowserNotificationFromEvent({
      title,
      body,
      conversationId,
      messageId: event.message_id,
    })
  }

  function handleIncomingNotificationPayload(payload, _origin = 'stream') {
    if (!payload || typeof payload !== 'object') return
    switch (payload.type) {
      case 'message.received':
        handleMessageNotificationEvent(payload)
        break
      case 'contact.request':
      case 'contact.accepted':
        handleContactNotificationEvent(payload)
        break
      case 'contact.blocked':
      case 'contact.unblocked':
        handleContactBlockEvent(payload)
        break
      default:
        break
    }
  }

  watch(
    browserNotificationsEnabled,
    (enabled) => {
      if (
        enabled &&
        typeof Notification !== 'undefined' &&
        Notification.permission === 'default' &&
        !notificationPermissionRequestPending
      ) {
        notificationPermissionRequestPending = true
        Notification.requestPermission()
          .catch(() => {})
          .finally(() => {
            notificationPermissionRequestPending = false
          })
      }
    },
    { immediate: true },
  )

  onMounted(() => {
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', handleBrowserPrefStorage)
      window.addEventListener('cova:browser-notifications', handleBrowserPrefBroadcast)
    }
    syncBrowserNotificationPreference()
  })

  onBeforeUnmount(() => {
    if (typeof window !== 'undefined') {
      window.removeEventListener('storage', handleBrowserPrefStorage)
      window.removeEventListener('cova:browser-notifications', handleBrowserPrefBroadcast)
    }
  })

  return {
    browserNotificationsEnabled,
    handleIncomingNotificationPayload,
    notifyNewIncomingMessage,
    syncBrowserNotificationPreference,
    handleBrowserPrefStorage,
    handleBrowserPrefBroadcast,
  }
}
