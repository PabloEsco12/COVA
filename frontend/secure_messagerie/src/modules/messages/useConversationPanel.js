import { computed, reactive, ref, watch } from 'vue'
import {
  updateConversation,
  leaveConversation,
  updateConversationMember,
  listConversationInvites,
  createConversationInvite,
  revokeConversationInvite,
} from '@/services/conversations'

export function useConversationPanel({
  selectedConversationId,
  selectedConversation,
  canManageConversation,
  conversations,
  conversationMeta,
  extractError,
  applyConversationPatch,
  applyMemberPayload,
  resetComposerState,
  clearPendingAttachments,
  resetSearchPanel,
  disconnectRealtime,
  selectConversation,
  formatAbsolute,
  conversationRoles,
}) {
  const showConversationPanel = ref(false)
  const conversationForm = reactive({ title: '', topic: '', archived: false })
  const savingConversation = ref(false)
  const conversationInfoError = ref('')
  const conversationInfoNotice = ref('')
  let conversationNoticeTimer = null
  const invites = ref([])
  const loadingInvites = ref(false)
  const inviteForm = reactive({ email: '', role: 'member', expiresInHours: 72 })
  const inviteBusy = ref(false)
  const inviteRevokeBusy = reactive({})
  const memberBusy = reactive({})
  const leavingConversation = ref(false)

  const conversationOwnerSummary = computed(() => {
    const owners =
      (selectedConversation.value?.members || []).filter((member) => member.role === 'owner') || []
    if (!owners.length) return 'Non défini'
    return owners.map((member) => member.displayName || member.email || 'Membre').join(', ')
  })

  function roleLabel(role) {
    const option = conversationRoles.find((entry) => entry.value === role)
    return option ? option.label : role
  }

  function syncConversationFormFromSelected() {
    const conv = selectedConversation.value
    if (!conv) return
    conversationForm.title = conv.title || ''
    conversationForm.topic = conv.topic || ''
    conversationForm.archived = Boolean(conv.archived)
  }

  function clearConversationNotice() {
    if (conversationNoticeTimer) {
      clearTimeout(conversationNoticeTimer)
      conversationNoticeTimer = null
    }
    conversationInfoNotice.value = ''
  }

  function setConversationNotice(message) {
    clearConversationNotice()
    if (message) {
      conversationInfoNotice.value = message
      conversationNoticeTimer = setTimeout(() => {
        conversationInfoNotice.value = ''
        conversationNoticeTimer = null
      }, 5000)
    }
  }

  async function openConversationPanel() {
    if (!selectedConversation.value) return
    conversationInfoError.value = ''
    clearConversationNotice()
    syncConversationFormFromSelected()
    showConversationPanel.value = true
    if (canManageConversation.value && selectedConversationId.value) {
      await loadConversationInvites(selectedConversationId.value)
    }
  }

  function closeConversationPanel() {
    showConversationPanel.value = false
    invites.value = []
    clearConversationNotice()
  }

  async function saveConversationSettings() {
    if (!selectedConversationId.value) return
    savingConversation.value = true
    conversationInfoError.value = ''
    clearConversationNotice()
    try {
      const payload = {
        title: conversationForm.title.trim() || null,
        topic: conversationForm.topic.trim() || null,
        archived: conversationForm.archived,
      }
      const data = await updateConversation(selectedConversationId.value, payload)
      applyConversationPatch(data)
      setConversationNotice('Conversation mise à jour.')
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible d'enregistrer la conversation.")
    } finally {
      savingConversation.value = false
    }
  }

  async function leaveCurrentConversation() {
    if (!selectedConversationId.value) return
    leavingConversation.value = true
    conversationInfoError.value = ''
    clearConversationNotice()
    const convId = selectedConversationId.value
    try {
      await leaveConversation(convId)
      conversations.value = conversations.value.filter((conv) => conv.id !== convId)
      delete conversationMeta[convId]
      showConversationPanel.value = false
      resetComposerState()
      clearPendingAttachments()
      resetSearchPanel()
      disconnectRealtime()
      selectConversation(null)
      const fallback = conversations.value[0]
      if (fallback) {
        selectConversation(fallback.id)
      }
    } catch (err) {
      conversationInfoError.value = extractError(err, 'Impossible de quitter la conversation.')
    } finally {
      leavingConversation.value = false
    }
  }

  async function loadConversationInvites(convId) {
    if (!canManageConversation.value || !convId) {
      invites.value = []
      return
    }
    loadingInvites.value = true
    conversationInfoError.value = ''
    clearConversationNotice()
    try {
      const data = await listConversationInvites(convId)
      invites.value = Array.isArray(data) ? data.map((invite) => mapInvite(invite)).filter(Boolean) : []
    } catch (err) {
      conversationInfoError.value = extractError(err, 'Impossible de charger les invitations.')
    } finally {
      loadingInvites.value = false
    }
  }

  async function submitInvite() {
    if (!selectedConversationId.value || !inviteForm.email.trim()) return
    inviteBusy.value = true
    conversationInfoError.value = ''
    clearConversationNotice()
    try {
      const payload = {
        email: inviteForm.email.trim(),
        role: inviteForm.role,
        expires_in_hours: inviteForm.expiresInHours,
      }
      const data = await createConversationInvite(selectedConversationId.value, payload)
      const mapped = mapInvite(data)
      if (mapped) {
        invites.value = [mapped, ...invites.value]
      }
      inviteForm.email = ''
      setConversationNotice('Invitation créée et envoyée.')
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible de créer l'invitation.")
    } finally {
      inviteBusy.value = false
    }
  }

  async function revokeInvite(inviteId) {
    if (!selectedConversationId.value || !inviteId) return
    inviteRevokeBusy[inviteId] = true
    conversationInfoError.value = ''
    clearConversationNotice()
    try {
      await revokeConversationInvite(selectedConversationId.value, inviteId)
      invites.value = invites.value.filter((invite) => invite.id !== inviteId)
      setConversationNotice('Invitation révoquée.')
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible de révoquer l'invitation.")
    } finally {
      delete inviteRevokeBusy[inviteId]
    }
  }

  async function updateMemberRole(member, role) {
    if (!selectedConversationId.value || !member?.id || !role || member.role === role) return
    memberBusy[member.id] = true
    conversationInfoError.value = ''
    clearConversationNotice()
    try {
      const data = await updateConversationMember(selectedConversationId.value, member.id, { role })
      applyMemberPayload(data)
      setConversationNotice('Rôle du membre mis à jour.')
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible de mettre à jour le membre.")
    } finally {
      delete memberBusy[member.id]
    }
  }

  async function muteMember(member, minutes = 60) {
    if (!selectedConversationId.value || !member?.id) return
    memberBusy[member.id] = true
    conversationInfoError.value = ''
    clearConversationNotice()
    const mutedUntil = new Date(Date.now() + minutes * 60000).toISOString()
    try {
      const data = await updateConversationMember(selectedConversationId.value, member.id, { muted_until: mutedUntil })
      applyMemberPayload(data)
      setConversationNotice(`Membre mis en sourdine pendant ${minutes} min.`)
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible de mettre le membre en sourdine.")
    } finally {
      delete memberBusy[member.id]
    }
  }

  async function unmuteMember(member) {
    if (!selectedConversationId.value || !member?.id) return
    memberBusy[member.id] = true
    conversationInfoError.value = ''
    clearConversationNotice()
    try {
      const data = await updateConversationMember(selectedConversationId.value, member.id, { muted_until: null })
      applyMemberPayload(data)
      setConversationNotice('Sourdine désactivée pour ce membre.')
    } catch (err) {
      conversationInfoError.value = extractError(err, "Impossible de rétablir le membre.")
    } finally {
      delete memberBusy[member.id]
    }
  }

  async function removeMember(member) {
    if (!selectedConversationId.value || !member?.id) return
    memberBusy[member.id] = true
    conversationInfoError.value = ''
    clearConversationNotice()
    try {
      const data = await updateConversationMember(selectedConversationId.value, member.id, { state: 'left' })
      applyMemberPayload(data)
      setConversationNotice('Membre retiré de la conversation.')
    } catch (err) {
      conversationInfoError.value = extractError(err, 'Impossible de retirer le membre.')
    } finally {
      delete memberBusy[member.id]
    }
  }

  function mapInvite(invite) {
    if (!invite) return null
    return {
      id: invite.id,
      email: invite.email,
      role: invite.role,
      token: invite.token,
      expiresAt: invite.expires_at ? new Date(invite.expires_at) : null,
      acceptedAt: invite.accepted_at ? new Date(invite.accepted_at) : null,
    }
  }

  function formatInviteStatus(invite) {
    if (!invite) return ''
    if (invite.acceptedAt) {
      return `Acceptée ${formatAbsolute(invite.acceptedAt)}`
    }
    if (invite.expiresAt) {
      return `Expire ${formatAbsolute(invite.expiresAt)}`
    }
    return ''
  }

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

  return {
    showConversationPanel,
    conversationForm,
    savingConversation,
    conversationInfoError,
    conversationInfoNotice,
    invites,
    loadingInvites,
    inviteForm,
    inviteBusy,
    inviteRevokeBusy,
    memberBusy,
    leavingConversation,
    conversationOwnerSummary,
    roleLabel,
    clearConversationNotice,
    setConversationNotice,
    openConversationPanel,
    closeConversationPanel,
    saveConversationSettings,
    leaveCurrentConversation,
    syncConversationFormFromSelected,
    loadConversationInvites,
    submitInvite,
    revokeInvite,
    updateMemberRole,
    muteMember,
    unmuteMember,
    removeMember,
    formatInviteStatus,
  }
}
