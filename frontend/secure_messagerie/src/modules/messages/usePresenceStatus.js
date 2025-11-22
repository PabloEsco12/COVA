import { computed, reactive, ref, watch } from 'vue'

import { api } from '@/utils/api'
import { broadcastProfileUpdate } from '@/utils/profile'
import { PRESENCE_STALE_MS, STATUS_LABELS, STATUS_PRESETS } from './constants'
import { memberUserId } from './mappers'

const OFFLINE_ENTRY = { status: 'offline', label: STATUS_LABELS.offline, lastSeen: null }

export function resolveAvailabilityFromStatus(message) {
  const code = deriveStatusFromMessage(message)
  if (code && STATUS_PRESETS[code]) {
    return code
  }
  return 'available'
}

function stripDiacritics(value) {
  return value.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
}

function deriveStatusFromMessage(message) {
  if (!message) return null
  const normalized = stripDiacritics(message).toLowerCase()
  if (normalized.includes('reunion') || normalized.includes('meeting')) return 'meeting'
  if (normalized.includes('pas deranger')) return 'dnd'
  if (normalized.includes('occup') || normalized.includes('busy')) return 'busy'
  if (normalized.includes('absent')) return 'away'
  if (normalized.includes('disponible')) return 'available'
  return null
}

function normalizePresenceStatus(status) {
  if (!status) return 'offline'
  const value = status.toLowerCase()
  if (value === 'online' || value === 'available') return 'online'
  if (value === 'meeting') return 'meeting'
  if (value === 'busy') return 'busy'
  if (value === 'dnd') return 'dnd'
  if (value === 'away') return 'away'
  return 'offline'
}

export function usePresenceStatus({
  conversations,
  selectedConversation,
  selectedConversationId,
  currentUserId,
  formatAbsolute,
}) {
  const myAvailability = ref(resolveAvailabilityFromStatus(readStoredStatusMessage()))
  const presenceSnapshot = ref({ users: [], timestamp: null })
  const conversationPresence = reactive({})
  const conversationPresenceSource = reactive({})
  const typingTimestamps = reactive({})
  const typingUsers = ref([])

  const presenceByUserId = computed(() => {
    const map = new Map()
    const snapshot = presenceSnapshot.value?.users || []
    snapshot.forEach((entry) => {
      if (!entry?.userId) return
      map.set(String(entry.userId), entry)
    })
    return map
  })

  const presenceSummary = computed(() => {
    const conv = selectedConversation.value
    if (!conv || !Array.isArray(conv.members)) return ''
    const snapshot = presenceSnapshot.value
    const snapshotUsers = snapshot?.users || []
    const snapshotTimestamp = snapshot?.timestamp instanceof Date ? snapshot.timestamp.getTime() : 0
    const isSnapshotFresh =
      snapshotUsers.length && snapshotTimestamp && Date.now() - snapshotTimestamp < PRESENCE_STALE_MS
    if (isSnapshotFresh) {
      const selfId = currentUserId.value ? String(currentUserId.value) : null
      const others = conv.members.filter((member) => memberUserId(member) !== selfId)
      if (!others.length) return ''
      if (others.length === 1) {
        const target = others[0]
        return memberPresenceText(target.userId || target.id)
      }
      const activeMembers = others.filter((member) => {
        const presence = memberPresence(member.userId || member.id)
        return presence.status === 'online' || presence.status === 'available'
      })
      if (!activeMembers.length) {
        return 'Tous les membres sont hors ligne'
      }
      if (activeMembers.length === 1) {
        return `${displayNameForUser(activeMembers[0].id)} est en ligne`
      }
      return `${activeMembers.length} membres en ligne`
    }
    if (conv.type === 'direct') {
      const manual = manualPresenceFromConversation(conv)
      if (manual) {
        return manual.label
      }
      const target =
        conv.members.find((member) => memberUserId(member) !== currentUserId.value) ||
        conv.members[0] ||
        null
      if (target) {
        return memberPresenceText(target.userId || target.id)
      }
    }
    return STATUS_LABELS.offline
  })

  const primaryParticipantPresence = computed(() => {
    const conv = selectedConversation.value
    if (!conv) {
      return { status: 'offline', label: STATUS_LABELS.offline, lastSeen: null }
    }
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    const target =
      conv.participants.find((member) => memberUserId(member) !== selfId) ||
      conv.members.find((member) => memberUserId(member) !== selfId)
    if (!target) {
      return { status: 'offline', label: STATUS_LABELS.offline, lastSeen: null }
    }
    return memberPresence(target.userId || target.id)
  })

  const typingIndicatorText = computed(() => {
    if (!typingUsers.value.length) return ''
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    const participants = typingUsers.value.filter((id) => id !== selfId)
    if (!participants.length) return ''
    if (participants.length === 1) {
      return `${displayNameForUser(participants[0])} est en train d'ecrire...`
    }
    return 'Plusieurs personnes ecrivent...'
  })

  watch(
    conversations,
    (list) => {
      list.forEach((conv) => {
        refreshManualPresenceForConversation(conv)
      })
    },
    { deep: true, immediate: true },
  )

  function displayNameForUser(userId) {
    if (!userId) return 'Participant'
    const conv = selectedConversation.value
    if (!conv || !Array.isArray(conv.members)) return 'Participant'
    const match = conv.members.find((member) => memberUserId(member) === String(userId))
    return match?.displayName || match?.email || 'Participant'
  }

  function memberPresence(memberId) {
    const key = memberId ? String(memberId) : null
    if (!key) {
      return OFFLINE_ENTRY
    }
    const base = presenceByUserId.value.get(key) || { status: 'offline', lastSeen: null }
    const member = findMemberById(key)
    const manual = deriveStatusFromMessage(member?.statusMessage || '')
    const status = manual || normalizePresenceStatus(base.status)
    const label =
      manual && member?.statusMessage
        ? member.statusMessage
        : STATUS_LABELS[status] || STATUS_LABELS.offline
    return { status, label, lastSeen: base.lastSeen || null }
  }

  function memberPresenceText(memberId) {
    const entry = memberPresence(memberId)
    if (entry.status === 'online' || entry.status === 'available') {
      return entry.label || STATUS_LABELS.online
    }
    if (entry.label && entry.label !== STATUS_LABELS.offline) {
      return entry.label
    }
    if (entry.lastSeen instanceof Date) {
      return `${STATUS_LABELS.offline} - vu ${formatAbsolute(entry.lastSeen)}`
    }
    return STATUS_LABELS.offline
  }

  function findMemberById(memberId) {
    const conv = selectedConversation.value
    if (!conv || !Array.isArray(conv.members)) return null
    const key = memberId ? String(memberId) : null
    if (!key) return null
    return (
      conv.members.find((member) => String(member.id) === key) ||
      conv.members.find((member) => memberUserId(member) === key) ||
      null
    )
  }

  function findConversationById(conversationId) {
    const targetId = String(conversationId)
    if (selectedConversation.value && String(selectedConversation.value.id) === targetId) {
      return selectedConversation.value
    }
    return conversations.value.find((entry) => String(entry.id) === targetId) || null
  }

  function findMemberInConversation(conversationId, memberId) {
    const conv = findConversationById(conversationId)
    if (!conv || !Array.isArray(conv.members)) return null
    const key = memberId ? String(memberId) : null
    if (!key) return null
    return (
      conv.members.find((member) => String(member.id) === key) ||
      conv.members.find((member) => memberUserId(member) === key) ||
      null
    )
  }

  function manualPresenceFromConversation(conv) {
    if (!conv || conv.type !== 'direct') return null
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    const target =
      (Array.isArray(conv.participants) &&
        conv.participants.find((member) => !selfId || memberUserId(member) !== selfId)) ||
      (Array.isArray(conv.members) &&
        conv.members.find((member) => !selfId || memberUserId(member) !== selfId))
    if (!target) return null
    return { status: 'offline', label: STATUS_LABELS.offline }
  }

  function manualPresenceForConversationId(convId) {
    const conv = findConversationById(convId)
    if (!conv) return null
    return manualPresenceFromConversation(conv)
  }

  function setConversationPresence(convId, entry, source = 'manual') {
    if (!convId) return
    const key = String(convId)
    conversationPresence[key] = entry
    conversationPresenceSource[key] = source
  }

  function getConversationPresenceSource(convId) {
    return conversationPresenceSource[String(convId)] || 'unknown'
  }

  function refreshManualPresenceForConversation(convOrId) {
    const conv =
      typeof convOrId === 'object' && convOrId !== null ? convOrId : findConversationById(convOrId)
    if (!conv) return
    if (conv.type !== 'direct') {
      if (!conversationPresence[conv.id]) {
        setConversationPresence(conv.id, OFFLINE_ENTRY, 'unknown')
      }
      return
    }
    if (getConversationPresenceSource(conv.id) === 'realtime') {
      return
    }
    const manual = manualPresenceFromConversation(conv)
    if (manual) {
      setConversationPresence(conv.id, manual, 'manual')
    } else if (!conversationPresence[conv.id]) {
      setConversationPresence(conv.id, OFFLINE_ENTRY, 'unknown')
    }
  }

  function refreshManualPresenceForAll() {
    conversations.value.forEach((conv) => refreshManualPresenceForConversation(conv))
  }

  function summarizePresenceEntries(entries) {
    if (!entries.length) {
      return OFFLINE_ENTRY
    }
    const normalized = entries.map((entry) => normalizePresenceStatus(entry.status))
    if (normalized.some((status) => status === 'meeting')) {
      return { status: 'meeting', label: STATUS_LABELS.meeting }
    }
    if (normalized.some((status) => status === 'busy' || status === 'dnd')) {
      return { status: 'busy', label: STATUS_LABELS.busy }
    }
    if (normalized.some((status) => status === 'online')) {
      return { status: 'online', label: STATUS_LABELS.online }
    }
    if (normalized.some((status) => status === 'away')) {
      return { status: 'away', label: STATUS_LABELS.away }
    }
    const offlineEntry = entries.find((entry) => entry.status === 'offline')
    if (offlineEntry?.label) {
      return { status: 'offline', label: offlineEntry.label, lastSeen: offlineEntry.lastSeen || null }
    }
    return OFFLINE_ENTRY
  }

  function applyPresencePayload(payload) {
    if (!payload) return
    const incomingConvId = payload.conversation_id ? String(payload.conversation_id) : null
    const currentConvId = selectedConversationId.value ? String(selectedConversationId.value) : null
    const isCurrentConversation = !incomingConvId || incomingConvId === currentConvId
    const convId = incomingConvId || currentConvId
    const selfId = currentUserId.value ? String(currentUserId.value) : null

    const rawUsers = Array.isArray(payload.users) ? payload.users : []
    const users = rawUsers
      .map((entry) => {
        const userId = entry?.user_id ? String(entry.user_id) : entry?.id ? String(entry.id) : ''
        if (!userId) return null
        if (selfId && userId === selfId) return null
        const baseStatus = normalizePresenceStatus(entry?.status || 'offline')
        const member = convId ? findMemberInConversation(convId, userId) : findMemberById(userId)
        const manualStatus = member?.statusMessage ? deriveStatusFromMessage(member.statusMessage) : null
        const status = manualStatus || baseStatus
        const label =
          manualStatus && member?.statusMessage
            ? member.statusMessage
            : STATUS_LABELS[status] || STATUS_LABELS.offline
        return {
          userId,
          status,
          label,
          lastSeen: entry?.last_seen ? new Date(entry.last_seen) : null,
        }
      })
      .filter(Boolean)
    if (isCurrentConversation) {
      presenceSnapshot.value = {
        users,
        timestamp: payload.timestamp ? new Date(payload.timestamp) : new Date(),
      }
    }
    if (convId) {
      let entry
      let source = 'realtime'
      if (users.length) {
        entry = summarizePresenceEntries(users)
      } else if (rawUsers.length) {
        entry = OFFLINE_ENTRY
      } else {
        const manual = manualPresenceForConversationId(convId)
        if (manual) {
          entry = manual
          source = 'manual'
        } else {
          entry = OFFLINE_ENTRY
          source = 'unknown'
        }
      }
      setConversationPresence(convId, entry, source)
    }
  }

  function resetRemoteTyping() {
    Object.keys(typingTimestamps).forEach((key) => delete typingTimestamps[key])
    typingUsers.value = []
  }

  function cleanupRemoteTyping() {
    const now = Date.now()
    let changed = false
    for (const [key, ts] of Object.entries(typingTimestamps)) {
      if (now - ts > 6000) {
        delete typingTimestamps[key]
        changed = true
      }
    }
    if (changed) {
      typingUsers.value = Object.keys(typingTimestamps)
    }
  }

  function handleRealtimeTyping(evt) {
    const eventName = evt?.event
    const userIdRaw = evt?.payload?.user_id
    const convId = evt?.payload?.conversation_id || evt?.conversation_id
    if (!selectedConversationId.value || !convId || String(convId) !== String(selectedConversationId.value)) {
      return
    }
    if (!eventName || !userIdRaw) return
    const userId = String(userIdRaw)
    if (currentUserId.value && String(currentUserId.value) === userId) return
    if (eventName === 'typing:start') {
      typingTimestamps[userId] = Date.now()
    } else if (eventName === 'typing:stop') {
      delete typingTimestamps[userId]
    }
    typingUsers.value = Object.keys(typingTimestamps)
  }

  function resetPresenceState() {
    presenceSnapshot.value = { users: [], timestamp: null }
    if (selectedConversationId.value) {
      setConversationPresence(selectedConversationId.value, OFFLINE_ENTRY, 'unknown')
      refreshManualPresenceForConversation(selectedConversationId.value)
    }
    resetRemoteTyping()
  }

  function readStoredStatusMessage() {
    try {
      return localStorage.getItem('status_message') || ''
    } catch {
      return ''
    }
  }

  function persistStatusMessage(value, codeHint) {
    const message = value || ''
    const code = codeHint || resolveAvailabilityFromStatus(message)
    try {
      if (message) {
        localStorage.setItem('status_message', message)
      } else {
        localStorage.removeItem('status_message')
      }
      if (code) {
        localStorage.setItem('status_code', code)
      } else {
        localStorage.removeItem('status_code')
      }
    } catch {}
  }

  function applyLocalStatusMessage(message) {
    const selfId = currentUserId.value ? String(currentUserId.value) : null
    if (!selfId) return
    conversations.value.forEach((conv) => {
      if (!Array.isArray(conv.members)) return
      conv.members.forEach((member) => {
        if (memberUserId(member) === selfId) {
          member.statusMessage = message || ''
        }
      })
    })
    if (selectedConversation.value && Array.isArray(selectedConversation.value.members)) {
      selectedConversation.value.members.forEach((member) => {
        if (memberUserId(member) === selfId) {
          member.statusMessage = message || ''
        }
      })
    }
    refreshManualPresenceForAll()
  }

  async function loadAvailabilityStatus() {
    try {
      const { data } = await api.get('/me/profile')
      const statusMessage = data?.status_message || ''
      const code = resolveAvailabilityFromStatus(statusMessage)
      persistStatusMessage(statusMessage, code)
      myAvailability.value = code
      applyLocalStatusMessage(statusMessage)
    } catch {
      myAvailability.value = 'available'
    }
  }

  async function onAvailabilityChange(value) {
    if (value === myAvailability.value) return
    const next = STATUS_PRESETS[value] ? value : 'available'
    const previous = myAvailability.value
    myAvailability.value = next
    const message = STATUS_PRESETS[next].message || ''
    try {
      await api.put('/me/profile', { status_message: message || null })
      persistStatusMessage(message, next)
      applyLocalStatusMessage(message)
      broadcastProfileUpdate({ status_message: message || null, status_code: next })
    } catch (err) {
      console.error('Impossible de mettre a jour le statut', err)
      myAvailability.value = previous
    }
  }

  function handleProfileBroadcast(event) {
    const detail = event?.detail || {}
    if (Object.prototype.hasOwnProperty.call(detail, 'status_message')) {
      const statusMessage = detail.status_message || ''
      const code = resolveAvailabilityFromStatus(statusMessage)
      persistStatusMessage(statusMessage, code)
      myAvailability.value = code
      applyLocalStatusMessage(statusMessage)
    }
  }

  return {
    myAvailability,
    presenceSnapshot,
    conversationPresence,
    presenceSummary,
    primaryParticipantPresence,
    typingIndicatorText,
    memberPresence,
    memberPresenceText,
    displayNameForUser,
    refreshManualPresenceForConversation,
    refreshManualPresenceForAll,
    resetPresenceState,
    applyPresencePayload,
    handleRealtimeTyping,
    cleanupRemoteTyping,
    loadAvailabilityStatus,
    onAvailabilityChange,
    handleProfileBroadcast,
  }
}
