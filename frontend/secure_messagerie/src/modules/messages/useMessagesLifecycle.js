import { nextTick, onBeforeUnmount, onMounted, watch } from 'vue'

export function useMessagesLifecycle({
  route,
  router,
  conversations,
  selectConversation,
  forwardPicker,
  forwardPickerRef,
  showConversationPanel,
  invites,
  clearPendingAttachments,
  resetComposerState,
  resetSearchPanel,
  syncConversationFormFromSelected,
  canManageConversation,
  loadConversationInvites,
  closeTransientMenus,
  cancelForwardSelection,
  closeDeleteDialog,
  messages,
  suppressAutoScroll,
  loadingOlderMessages,
  scrollToBottom,
  selectedConversationId,
  endCall,
  disconnectRealtime,
  loadConversations,
  loadAvailabilityStatus,
  cleanupRemoteTyping,
  handleProfileBroadcast,
  processNotificationPayload,
  ensureMessageVisible,
  reactionPickerFor,
  messageMenuOpen,
}) {
  let typingCleanupTimer = null

  const emitActiveConversation = (convId) => {
    if (typeof window === 'undefined') return
    window.dispatchEvent(new CustomEvent('cova:active-conversation', { detail: { convId } }))
  }

  const handleGlobalNotificationEvent = (event) => {
    const payload = event?.detail
    if (!payload) return
    processNotificationPayload(payload, payload.__origin || 'bridge')
  }

  const handleExternalConversationRequest = async (event) => {
    const targetId = event?.detail?.id
    if (!targetId) return
    await selectConversation(String(targetId))
    const messageId = event.detail?.messageId
    if (messageId) {
      await nextTick()
      await ensureMessageVisible(messageId)
    }
  }

  const handleDocumentClick = () => {
    if (forwardPicker.open) {
      cancelForwardSelection()
      return
    }
    if (!reactionPickerFor.value && !messageMenuOpen.value) return
    closeTransientMenus()
  }

  const handleDocumentKeydown = (event) => {
    if (event.key !== 'Escape') return
    if (forwardPicker.open) {
      event.preventDefault()
      cancelForwardSelection()
      return
    }
    if (!reactionPickerFor.value && !messageMenuOpen.value) return
    event.preventDefault()
    closeTransientMenus()
  }

  watch(
    () => route.query.conversation,
    (id) => {
      if (!id) return
      const convId = String(id)
      if (conversations.value.some((conv) => conv.id === convId)) {
        selectConversation(convId)
      }
    },
  )

  watch(
    () => forwardPicker.open,
    (open) => {
      if (open) {
        nextTick(() => {
          try {
            forwardPickerRef.value?.inputRef?.focus?.()
          } catch {}
        })
      }
    },
  )

  watch(selectedConversationId, async (id) => {
    closeTransientMenus()
    if (forwardPicker.open) {
      cancelForwardSelection()
    }
    closeDeleteDialog()
    if (!id) {
      showConversationPanel.value = false
      invites.value = []
      clearPendingAttachments()
      resetComposerState()
      resetSearchPanel()
      return
    }
    router.replace({ query: { ...route.query, conversation: id } }).catch(() => {})
    emitActiveConversation(id)
    resetComposerState()
    resetSearchPanel()
    if (showConversationPanel.value) {
      syncConversationFormFromSelected()
      if (canManageConversation.value) {
        loadConversationInvites(id)
      } else {
        invites.value = []
      }
    }
  })

  watch(showConversationPanel, (open) => {
    if (open) {
      syncConversationFormFromSelected()
      if (canManageConversation.value && selectedConversationId.value) {
        loadConversationInvites(selectedConversationId.value)
      } else {
        invites.value = []
      }
    }
  })

  watch(canManageConversation, (canManage) => {
    if (!showConversationPanel.value) return
    if (canManage && selectedConversationId.value) {
      loadConversationInvites(selectedConversationId.value)
    } else {
      invites.value = []
    }
  })

  watch(
    () => messages.value.length,
    async () => {
      await nextTick()
      if (suppressAutoScroll.value) {
        suppressAutoScroll.value = false
        return
      }
      if (!loadingOlderMessages.value) {
        scrollToBottom()
      }
    },
  )

  onMounted(async () => {
    await loadConversations()
    await loadAvailabilityStatus()
    if (typeof window !== 'undefined') {
      document.addEventListener('click', handleDocumentClick)
      document.addEventListener('keydown', handleDocumentKeydown)
      window.addEventListener('cova:profile-update', handleProfileBroadcast)
      window.addEventListener('cova:notification-event', handleGlobalNotificationEvent)
      window.addEventListener('cova:open-conversation', handleExternalConversationRequest)
    }
    typingCleanupTimer = setInterval(cleanupRemoteTyping, 2000)
  })

  onBeforeUnmount(() => {
    endCall(true)
    disconnectRealtime()
    if (typingCleanupTimer) {
      clearInterval(typingCleanupTimer)
      typingCleanupTimer = null
    }
    if (typeof window !== 'undefined') {
      document.removeEventListener('click', handleDocumentClick)
      document.removeEventListener('keydown', handleDocumentKeydown)
      window.removeEventListener('cova:profile-update', handleProfileBroadcast)
      window.removeEventListener('cova:notification-event', handleGlobalNotificationEvent)
      window.removeEventListener('cova:open-conversation', handleExternalConversationRequest)
    }
  })
}
