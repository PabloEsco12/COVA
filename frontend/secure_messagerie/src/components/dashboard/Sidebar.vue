<template>
  <nav :class="['sidebar d-flex flex-column p-3', isDark ? 'sidebar-dark' : 'sidebar-light']">
    <router-link
      to="/dashboard"
      :class="['mb-4 text-center text-decoration-none brand-link', isDark ? 'text-light' : 'text-dark']"
    >
      <img src="@/assets/logo_COVA.png" alt="COVA" width="48" />
      <h4 class="mt-2 fw-bold">COVA</h4>
      <small class="tagline">Messagerie chiffrée de confiance</small>
    </router-link>

    <SidebarProfileCard
      :pseudo="pseudo"
      :avatar-url="avatarUrl"
      :initials="initials"
      :user-status-code="userStatusCode"
      :user-status-label="userStatusLabel"
      :is-online="isOnline"
      @avatar-error="onAvatarError"
    />

    <SidebarPrimaryActions
      @start-conversation="startConversation"
      @invite-contact="inviteContact"
    />

    <SidebarQuickLinks :links="quickLinks" />

    <SidebarInsights
      :formatted-today="formattedToday"
      :formatted-time="formattedTime"
      :highlights="insightHighlights"
      :recommendations="insightRecommendations"
      :last-audit-text="lastAuditText"
      :insights-refreshing="insightsRefreshing"
      @refresh-insights="refreshInsights"
    />

    <SidebarSecurity
      :security-settings="securitySettings"
      :last-audit-text="lastAuditText"
      @go-security="goToSecurity"
    />

    <SidebarFooter
      :is-online="isOnline"
      :is-dark="isDark"
      :unread-count="unreadCount"
      @toggle-dark="$emit('toggle-dark')"
    />
  </nav>
</template>
<script setup>
import { ref, onMounted, onBeforeUnmount, defineProps, toRefs, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, backendBase } from '@/utils/api'
import { computeAvatarInitials, normalizeAvatarUrl } from '@/utils/profile'
import SidebarFooter from '../sidebar/SidebarFooter.vue'
import SidebarInsights from '../sidebar/SidebarInsights.vue'
import SidebarPrimaryActions from '../sidebar/SidebarPrimaryActions.vue'
import SidebarProfileCard from '../sidebar/SidebarProfileCard.vue'
import SidebarQuickLinks from '../sidebar/SidebarQuickLinks.vue'
import SidebarSecurity from '../sidebar/SidebarSecurity.vue'

const STATUS_LABELS = {
  available: 'Disponible',
  away: 'Absent',
  meeting: 'En réunion',
  busy: 'Occupé',
  dnd: 'Ne pas déranger',
  offline: 'Hors ligne',
}

const props = defineProps({
  isDark: Boolean
})

defineEmits(['toggle-dark'])

const { isDark } = toRefs(props)
const router = useRouter()

const userId = Number(localStorage.getItem('user_id') || 0)
const unreadCount = ref(0)
const pendingContacts = ref(readPendingContactsFromCache())
const statusMessage = ref(readStatusMessageFromCache())
const statusCodeHint = ref(readStatusCodeFromCache())
const unreadByConversation = ref({})
const activeConversationId = ref(null)
const pseudo = ref('Utilisateur')
const avatarUrl = ref(null)
const isOnline = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
const securitySettings = ref({
  totpEnabled: false,
  notificationLogin: false
})
const lastAuditLog = ref(null)
const nowClock = ref(new Date())
let clockTimer = null

const initials = computed(() =>
  computeAvatarInitials({
    displayName: pseudo.value,
    fallback: 'C',
  }),
)
const lastAuditText = computed(() => {
  if (!lastAuditLog.value) return ''
  const { timestamp, ip } = lastAuditLog.value
  const relative = formatRelativeTime(timestamp)
  if (relative && ip) {
    return `${relative} · IP ${ip}`
  }
  return relative || (ip ? `IP ${ip}` : '')
})

const quickLinks = computed(() => [
  {
    to: '/dashboard/messages',
    label: 'Messages',
    hint: unreadCount.value > 0 ? `${unreadCount.value} non lus` : 'Flux sécurisé',
    icon: 'bi bi-chat-dots-fill',
  },
  {
    to: '/dashboard/contacts',
    label: 'Contacts',
    hint:
      pendingContacts.value > 0
        ? `${pendingContacts.value} demande${pendingContacts.value > 1 ? 's' : ''} en attente`
        : 'Équipe & partenaires',
    icon: 'bi bi-person-lines-fill',
    badge:
      pendingContacts.value > 0
        ? pendingContacts.value > 99
          ? '99+'
          : String(pendingContacts.value)
        : null,
    badgeVariant: pendingContacts.value > 0 ? 'warning' : null,
  },
  {
    to: '/dashboard/devices',
    label: 'Appareils',
    hint: 'Sessions approuvées',
    icon: 'bi bi-laptop',
  },
  {
    to: '/dashboard/settings',
    label: 'Paramètres',
    hint: 'Sécurité & alertes',
    icon: 'bi bi-gear-fill',
  },
  {
    to: '/dashboard/faq',
    label: 'FAQ',
    hint: 'Conseils & support',
    icon: 'bi bi-question-circle-fill',
  },
])

const formattedToday = computed(() =>
  nowClock.value.toLocaleDateString('fr-FR', { weekday: 'long', month: 'long', day: 'numeric' }),
)
const formattedTime = computed(() =>
  nowClock.value.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
)

const numberFormatter = typeof Intl !== 'undefined' ? new Intl.NumberFormat('fr-FR') : null
const activeConversationsCount = computed(() => Object.keys(unreadByConversation.value || {}).length)
const insightsRefreshing = ref(false)
const userStatusCode = computed(() => deriveStatusCode(statusMessage.value, statusCodeHint.value))
const userStatusLabel = computed(() => {
  const message = (statusMessage.value || '').trim()
  if (message) return message
  return STATUS_LABELS[userStatusCode.value] || STATUS_LABELS.available
})

function normalizePendingCount(value) {
  const parsed = Math.floor(Number(value) || 0)
  if (!Number.isFinite(parsed) || parsed < 0) {
    return 0
  }
  return parsed
}

function readPendingContactsFromCache() {
  if (typeof window === 'undefined') return 0
  try {
    const raw = window.localStorage.getItem('pending_contacts')
    return normalizePendingCount(raw)
  } catch {
    return 0
  }
}

function readStatusMessageFromCache() {
  if (typeof window === 'undefined') return ''
  try {
    return window.localStorage.getItem('status_message') || ''
  } catch {
    return ''
  }
}

function readStatusCodeFromCache() {
  if (typeof window === 'undefined') return 'available'
  try {
    return window.localStorage.getItem('status_code') || 'available'
  } catch {
    return 'available'
  }
}

function normalizeStatusText(value) {
  return value
    ? value
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim()
    : ''
}

function deriveStatusCode(message, fallback = 'available') {
  const normalized = normalizeStatusText(message)
  if (!normalized) return fallback || 'available'
  if (normalized === 'disponible') return 'available'
  if (normalized === 'absent') return 'away'
  if (normalized === 'En réunion') return 'meeting'
  if (normalized === 'Occupé') return 'busy'
  if (normalized === 'Ne pas déranger') return 'dnd'
  if (normalized === 'hors ligne' || normalized === 'horsligne') return 'offline'
  return fallback || 'available'
}

function updateStatusMessage(value, { persist = false, code } = {}) {
  statusMessage.value = value || ''
  const derived = code || deriveStatusCode(statusMessage.value, statusCodeHint.value)
  statusCodeHint.value = derived
  if (persist) {
    cacheStatusPayload(statusMessage.value, derived)
  }
}

function cacheStatusPayload(message, code) {
  if (typeof window === 'undefined') return
  try {
    if (message) {
      window.localStorage.setItem('status_message', message)
    } else {
      window.localStorage.removeItem('status_message')
    }
    if (code) {
      window.localStorage.setItem('status_code', code)
    } else {
      window.localStorage.removeItem('status_code')
    }
  } catch {
    /* ignore */
  }
}

function applyPendingContacts(value, { persist = true } = {}) {
  const normalized = normalizePendingCount(value)
  pendingContacts.value = normalized
  if (!persist || typeof window === 'undefined') return
  try {
    if (normalized > 0) {
      window.localStorage.setItem('pending_contacts', String(normalized))
    } else {
      window.localStorage.removeItem('pending_contacts')
    }
  } catch {
    /* ignore storage failures */
  }
}

function formatStatNumber(value) {
  const safe = Number(value) || 0
  if (!numberFormatter) return String(safe)
  return numberFormatter.format(safe)
}

const insightHighlights = computed(() => {
  const totalUnread = Number(unreadCount.value) || 0
  const pending = Number(pendingContacts.value) || 0
  const activeConvs = Number(activeConversationsCount.value) || 0
  return [
    {
      id: 'inbox',
      label: 'Messages',
      value: formatStatNumber(totalUnread),
      hint: totalUnread ? `${totalUnread} à traiter` : 'Tous lus',
    },
    {
      id: 'invites',
      label: 'Invitations',
      value: formatStatNumber(pending),
      hint: pending ? 'Contacts à valider' : 'Aucune demande',
    },
    {
      id: 'threads',
      label: 'Conversations',
      value: formatStatNumber(activeConvs),
      hint: activeConvs ? 'Suivi actif' : 'Aucun fil suivi',
    },
  ]
})

const insightRecommendations = computed(() => {
  const items = []
  const totalUnread = Number(unreadCount.value) || 0
  const pending = Number(pendingContacts.value) || 0
  const totpActive = !!securitySettings.value.totpEnabled
  const online = !!isOnline.value

  if (!totpActive) {
    items.push({
      id: 'totp',
      icon: 'bi bi-shield-exclamation',
      title: 'Activez MFA',
      description: 'Ajoutez une vérification TOTP pour sécuriser chaque connexion.',
      variant: 'danger',
    })
  }

  if (pending > 0) {
    items.push({
      id: 'pending',
      icon: 'bi bi-people',
      title: 'Invitations en attente',
      description: 'Approuvez ou refusez les nouvelles demandes de contact.',
      badge: pending > 99 ? '99+' : String(pending),
      variant: 'warning',
    })
  }

  if (totalUnread > 0) {
    items.push({
      id: 'unread',
      icon: 'bi bi-chat-left-text',
      title: 'Messages prioritaires',
      description: totalUnread === 1 ? '1 message attend votre réponse.' : `${totalUnread} messages attendent votre réponse.`,
      variant: 'info',
    })
  }

  if (!online) {
    items.push({
      id: 'offline',
      icon: 'bi bi-wifi-off',
      title: 'Connexion instable',
      description: 'Certaines alertes seront envoyées dès que le canal sera rétabli.',
      variant: 'muted',
    })
  }

  if (!items.length) {
    items.push({
      id: 'clear',
      icon: 'bi bi-check2-circle',
      title: 'Tout est sécurisé',
      description: 'Aucune action urgente. Continuez vos échanges en toute confiance.',
      variant: 'success',
    })
  }

  return items.slice(0, 3)
})

const updateNetworkStatus = () => {
  if (typeof navigator !== 'undefined') {
    isOnline.value = navigator.onLine
  }
}

const startConversation = () => {
  router.push({ path: '/dashboard/messages', query: { compose: 'new' } })
}

const inviteContact = () => {
  router.push({ path: '/dashboard/contacts', query: { add: '1' } })
}

const goToSecurity = () => {
  router.push({ path: '/dashboard/settings', query: { section: 'security' } })
}

const onAvatarError = () => {
  avatarUrl.value = null
  try {
    localStorage.removeItem('avatar_url')
  } catch (e) {
    /* ignore */
  }
}

const computeUnreadTotal = map =>
  Object.values(map || {}).reduce((sum, value) => sum + Math.max(0, Number(value) || 0), 0)

function setUnreadMap(map, { persist = true } = {}) {
  const normalized = {}
  if (map && typeof map === 'object') {
    for (const [key, rawValue] of Object.entries(map)) {
      const convId = String(key)
      const count = Math.max(0, Number(rawValue) || 0)
      if (count > 0) normalized[convId] = count
    }
  }
  unreadByConversation.value = normalized
  unreadCount.value = computeUnreadTotal(normalized)
  if (persist) {
    try {
      localStorage.setItem('unread_counts', JSON.stringify(normalized))
    } catch {}
  }
}

function applyUnreadSummary(summary) {
  const map = summary?.by_conversation || summary?.byConversation || summary || {}
  setUnreadMap(map)
  if (summary && Object.prototype.hasOwnProperty.call(summary, 'total')) {
    const total = Number(summary.total)
    if (!Number.isNaN(total)) unreadCount.value = total
  }
}

async function loadUnreadSummary() {
  try {
    const res = await api.get(`/messages/unread_summary`)
    applyUnreadSummary(res.data || {})
  } catch (error) {
    try {
      const raw = JSON.parse(localStorage.getItem('unread_counts') || '{}') || {}
      setUnreadMap(raw, { persist: false })
    } catch {
      setUnreadMap({}, { persist: false })
    }
  }
}

async function loadPendingContactsSummary() {
  try {
    const res = await api.get(`/contacts`, { params: { status: 'pending' } })
    const list = Array.isArray(res.data) ? res.data : []
    applyPendingContacts(list.length)
  } catch {
    applyPendingContacts(readPendingContactsFromCache(), { persist: false })
  }
}

async function loadProfileStatus() {
  try {
    const res = await api.get(`/me/profile`)
    const next = res.data?.status_message || ''
    const code = deriveStatusCode(next, statusCodeHint.value)
    updateStatusMessage(next, { persist: true, code })
  } catch {
    /* ignore */
  }
}

function incrementUnread(convId, delta = 1) {
  const id = Number(convId)
  if (!id) return
  const key = String(id)
  const current = Number(unreadByConversation.value[key] || 0)
  const next = current + Number(delta || 0)
  const map = { ...unreadByConversation.value }
  if (next > 0) map[key] = next
  else delete map[key]
  setUnreadMap(map)
}

function clearUnread(convId) {
  const id = Number(convId)
  if (!id) return
  const key = String(id)
  if (!unreadByConversation.value[key]) return
  const map = { ...unreadByConversation.value }
  delete map[key]
  setUnreadMap(map)
}

function handleUnreadEvent(event) {
  applyUnreadSummary(event?.detail || {})
}

function handleActiveConversationEvent(event) {
  const convId = Number(event?.detail?.convId ?? 0)
  activeConversationId.value = convId > 0 ? convId : null
}

function handleUnreadStorage(event) {
  if (event?.key !== 'unread_counts') return
  try {
    const map = event.newValue ? JSON.parse(event.newValue) || {} : {}
    setUnreadMap(map, { persist: false })
  } catch {
    setUnreadMap({}, { persist: false })
  }
}

function handleStatusStorage(event) {
  if (!event) return
  if (event.key === 'status_message') {
    const derived = deriveStatusCode(event.newValue || '', statusCodeHint.value)
    updateStatusMessage(event.newValue || '', { persist: false, code: derived })
  } else if (event.key === 'status_code') {
    statusCodeHint.value = event.newValue || 'available'
  }
}

function handlePendingContactsEvent(event) {
  const detail = event?.detail || {}
  if (Object.prototype.hasOwnProperty.call(detail, 'pending')) {
    applyPendingContacts(detail.pending)
    return
  }
  if (Object.prototype.hasOwnProperty.call(detail, 'delta')) {
    applyPendingContacts(pendingContacts.value + Number(detail.delta || 0))
    return
  }
  if (detail.refresh) {
    loadPendingContactsSummary()
  }
}

function handlePendingContactsStorage(event) {
  if (event?.key !== 'pending_contacts') return
  applyPendingContacts(event.newValue, { persist: false })
}

function handleProfileUpdateEvent(event) {
  const payload = event?.detail || {}
  if (Object.prototype.hasOwnProperty.call(payload, 'display_name')) {
    const next = (payload.display_name || '').trim()
    pseudo.value = next || 'Utilisateur'
    try {
      if (next) {
        localStorage.setItem('pseudo', next)
      } else {
        localStorage.removeItem('pseudo')
      }
    } catch {}
  }
  if (Object.prototype.hasOwnProperty.call(payload, 'avatar_url')) {
    const nextAvatar = normalizeAvatarUrl(payload.avatar_url || null, { baseUrl: backendBase })
    avatarUrl.value = nextAvatar
    try {
      if (nextAvatar) {
        localStorage.setItem('avatar_url', nextAvatar)
      } else {
        localStorage.removeItem('avatar_url')
      }
    } catch {}
  }
  if (Object.prototype.hasOwnProperty.call(payload, 'status_message')) {
    updateStatusMessage(payload.status_message || '', {
      persist: true,
      code: payload.status_code || undefined,
    })
  }
}

async function fetchSecuritySnapshot() {
  try {
    const securityRes = await api.get(`/me/security`)
    securitySettings.value = {
      totpEnabled: !!securityRes.data?.totp_enabled,
      notificationLogin: !!securityRes.data?.notification_login,
    }
  } catch {
    securitySettings.value = {
      totpEnabled: false,
      notificationLogin: false,
    }
  }
}

async function fetchAuditPreview() {
  try {
    const auditRes = await api.get(`/me/audit`)
    if (Array.isArray(auditRes.data) && auditRes.data.length > 0) {
      lastAuditLog.value = auditRes.data[0]
    } else {
      lastAuditLog.value = null
    }
  } catch {
    lastAuditLog.value = null
  }
}

async function refreshInsights() {
  if (insightsRefreshing.value) return
  insightsRefreshing.value = true
  try {
    await Promise.allSettled([
      loadUnreadSummary(),
      loadPendingContactsSummary(),
      loadProfileStatus(),
      fetchSecuritySnapshot(),
      fetchAuditPreview(),
    ])
  } finally {
    insightsRefreshing.value = false
  }
}











onMounted(async () => {
  pseudo.value = localStorage.getItem('pseudo') || 'Utilisateur'
  avatarUrl.value = normalizeAvatarUrl(localStorage.getItem('avatar_url'), { baseUrl: backendBase })
  clockTimer = setInterval(() => {
    nowClock.value = new Date()
  }, 60000)

  if (typeof window !== 'undefined') {
    window.addEventListener('online', updateNetworkStatus)
    window.addEventListener('offline', updateNetworkStatus)
    window.addEventListener('cova:unread', handleUnreadEvent)
    window.addEventListener('cova:active-conversation', handleActiveConversationEvent)
    window.addEventListener('cova:profile-update', handleProfileUpdateEvent)
    window.addEventListener('storage', handleUnreadStorage)
    window.addEventListener('storage', handlePendingContactsStorage)
    window.addEventListener('storage', handleStatusStorage)
    window.addEventListener('cova:contacts-pending', handlePendingContactsEvent)
  }

  await Promise.all([loadUnreadSummary(), loadPendingContactsSummary(), loadProfileStatus()])

  const token = localStorage.getItem('access_token')
  if (!token) {
    return
  }

  try {
    const profileRes = await api.get(`/me`)
    if (profileRes.data?.pseudo) {
      pseudo.value = profileRes.data.pseudo
      localStorage.setItem('pseudo', profileRes.data.pseudo)
    }
    const apiAvatar = normalizeAvatarUrl(
      profileRes.data?.avatar_url ||
        (profileRes.data?.avatar ? `/static/avatars/${profileRes.data.avatar}` : null),
      { baseUrl: backendBase },
    )
    if (apiAvatar) {
      avatarUrl.value = apiAvatar
      localStorage.setItem('avatar_url', apiAvatar)
    } else {
      avatarUrl.value = null
      localStorage.removeItem('avatar_url')
    }
  } catch (e) {
    // ignore
  }

  await fetchSecuritySnapshot()
  await fetchAuditPreview()
})

onBeforeUnmount(() => {
  if (clockTimer) {
    clearInterval(clockTimer)
    clockTimer = null
  }
  if (typeof window !== 'undefined') {
    window.removeEventListener('online', updateNetworkStatus)
    window.removeEventListener('offline', updateNetworkStatus)
    window.removeEventListener('cova:unread', handleUnreadEvent)
    window.removeEventListener('cova:active-conversation', handleActiveConversationEvent)
    window.removeEventListener('cova:profile-update', handleProfileUpdateEvent)
    window.removeEventListener('storage', handleUnreadStorage)
    window.removeEventListener('storage', handlePendingContactsStorage)
    window.removeEventListener('storage', handleStatusStorage)
    window.removeEventListener('cova:contacts-pending', handlePendingContactsEvent)
  }
})

function formatRelativeTime(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return ''

  const diffMs = date.getTime() - Date.now()
  const diffSeconds = Math.round(diffMs / 1000)

  const rtf = typeof Intl !== 'undefined' && Intl.RelativeTimeFormat
    ? new Intl.RelativeTimeFormat('fr', { numeric: 'auto' })
    : null

  const divisions = [
    { amount: 60, unit: 'second' },
    { amount: 60, unit: 'minute' },
    { amount: 24, unit: 'hour' },
    { amount: 7, unit: 'day' },
    { amount: 4.34524, unit: 'week' },
    { amount: 12, unit: 'month' },
    { amount: Number.POSITIVE_INFINITY, unit: 'year' }
  ]

  let duration = Math.abs(diffSeconds)
  let unit = 'second'

  for (const division of divisions) {
    if (duration < division.amount) {
      break
    }
    duration /= division.amount
    unit = division.unit
  }

  duration = Math.round(duration) * Math.sign(diffSeconds)

  if (rtf) {
    return rtf.format(duration, unit)
  }

  if (typeof Intl !== 'undefined' && Intl.DateTimeFormat) {
    const formatter = new Intl.DateTimeFormat('fr-FR', {
      dateStyle: 'short',
      timeStyle: 'short'
    })
    return formatter.format(date)
  }

  return date.toISOString()
}
</script>
<style src="../sidebar/Sidebar.css"></style>



