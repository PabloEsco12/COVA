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

    <section class="sidebar-profile mb-4">
      <div class="profile-avatar">
        <img
          v-if="avatarUrl"
          :src="avatarUrl"
          alt="Avatar utilisateur"
          width="48"
          height="48"
          class="rounded-circle"
          @error="onAvatarError"
        />
        <div v-else class="avatar-fallback">{{ initials }}</div>
      </div>
      <div class="profile-details">
        <div class="profile-heading">
          <h6 class="profile-name mb-0" :title="pseudo">{{ pseudo }}</h6>
          <span class="badge encryption-badge">
            <i class="bi bi-lock-fill me-1"></i>
            Chiffré
          </span>
        </div>
        <p class="profile-status-line">
          <span class="status-dot" :class="`status-${userStatusCode}`"></span>
          <span class="status-text">{{ userStatusLabel }}</span>
        </p>
        <p class="profile-connection" :class="{ 'is-offline': !isOnline }">
          {{ isOnline ? 'Connexion sécurisée' : 'Connexion instable' }}
        </p>
      </div>
    </section>

    <section class="sidebar-actions mb-4">
      <button type="button" class="btn btn-primary w-100 mb-2" @click="startConversation">
        <i class="bi bi-pencil-square me-2"></i>
        Nouvelle conversation
      </button>
      <button type="button" class="btn btn-outline-primary w-100" @click="inviteContact">
        <i class="bi bi-person-plus me-2"></i>
        Inviter un contact
      </button>
    </section>

    <section class="sidebar-section quick-links">
      <p class="sidebar-section-title">Raccourcis sécurisés</p>
      <div class="quick-links-grid">
        <router-link
          v-for="link in quickLinks"
          :key="link.to"
          class="quick-link"
          :to="link.to"
        >
          <div class="quick-link__icon">
            <i :class="link.icon"></i>
          </div>
          <div class="quick-link__body">
            <span class="quick-link__label">
              {{ link.label }}
              <span
                v-if="link.badge"
                :class="['quick-link__badge', link.badgeVariant ? `quick-link__badge--${link.badgeVariant}` : null]"
              >
                {{ link.badge }}
              </span>
            </span>
            <small class="quick-link__hint">{{ link.hint }}</small>
          </div>
          <i class="bi bi-arrow-right-short quick-link__chevron"></i>
        </router-link>
      </div>
    </section>

    <section class="sidebar-insights mb-4">
      <div class="insights-header">
        <div>
          <p class="insights-eyebrow">Vue sécurité</p>
          <h5 class="mb-0">{{ formattedToday }}</h5>
          <small class="text-muted">{{ formattedTime }}</small>
        </div>
        <button
          class="btn btn-outline-light btn-sm"
          :disabled="insightsRefreshing"
          @click="refreshInsights"
        >
          <span v-if="insightsRefreshing" class="spinner-border spinner-border-sm me-1"></span>
          Rafraîchir
        </button>
      </div>
      <div class="insights-summary mt-3">
        <div
          v-for="highlight in insightHighlights"
          :key="highlight.id"
          class="insight-highlight"
        >
          <p class="highlight-label">{{ highlight.label }}</p>
          <p class="highlight-value">{{ highlight.value }}</p>
          <small>{{ highlight.hint }}</small>
        </div>
      </div>
      <div class="insight-actions mt-3">
        <article v-for="action in insightRecommendations" :key="action.id" class="insight-action">
          <div class="insight-action__icon" :class="`variant-${action.variant || 'info'}`">
            <i :class="action.icon"></i>
          </div>
          <div class="insight-action__body">
            <p class="insight-action__title mb-1">
              {{ action.title }}
              <span v-if="action.badge" class="insight-action__badge">{{ action.badge }}</span>
            </p>
            <small class="insight-action__description">{{ action.description }}</small>
          </div>
        </article>
      </div>
      <div v-if="lastAuditText" class="insight-activity mt-3">
        <i class="bi bi-activity me-2"></i>
        <span>{{ lastAuditText }}</span>
      </div>
    </section>

    <section class="sidebar-section mt-4">
      <p class="sidebar-section-title">Sécurité & confidentialité</p>
      <ul class="list-unstyled sidebar-security">
        <li class="security-item">
          <div class="security-icon info">
            <i class="bi bi-shield-check"></i>
          </div>
          <div>
            <span class="label">Chiffrement de bout en bout</span>
            <small class="text-muted">AES-256/GCM actif</small>
          </div>
        </li>
        <li class="security-item">
          <div :class="['security-icon', securitySettings.totpEnabled ? 'success' : 'warning']">
            <i :class="securitySettings.totpEnabled ? 'bi bi-shield-lock' : 'bi bi-exclamation-triangle'"></i>
          </div>
          <div>
            <span class="label">Double authentification</span>
            <small :class="securitySettings.totpEnabled ? 'text-success' : 'text-warning'">
              {{ securitySettings.totpEnabled ? 'Activée' : 'Désactivée' }}
            </small>
          </div>
        </li>
        <li class="security-item">
          <div :class="['security-icon', securitySettings.notificationLogin ? 'info' : 'muted']">
            <i class="bi bi-bell"></i>
          </div>
          <div>
            <span class="label">Alertes de connexion</span>
            <small :class="securitySettings.notificationLogin ? 'text-primary' : 'text-muted'">
              {{ securitySettings.notificationLogin ? 'Activées' : 'Aucune alerte' }}
            </small>
          </div>
        </li>
      </ul>

      <div v-if="lastAuditText" class="audit-card mt-3">
        <div class="audit-icon">
          <i class="bi bi-activity"></i>
        </div>
        <div>
          <span class="fw-semibold d-block">Dernière activité</span>
          <small class="text-muted">{{ lastAuditText }}</small>
        </div>
      </div>

      <button type="button" class="manage-security" @click="goToSecurity">
        <i class="bi bi-shield-lock me-2"></i>
        Gérer mes paramètres de sécurité
      </button>
    </section>

    <div class="sidebar-footer mt-auto pt-4">
      <div class="connection-status mb-3">
        <span class="status-indicator" :class="isOnline ? 'bg-success' : 'bg-warning'"></span>
        <span class="ms-2">{{ isOnline ? 'Réseau protégé' : 'Connexion instable' }}</span>
      </div>
      <button
        type="button"
        class="btn btn-sm theme-toggle"
        :class="isDark ? 'btn-outline-light' : 'btn-outline-secondary'"
        @click="$emit('toggle-dark')"
      >
        <i :class="isDark ? 'bi bi-sun' : 'bi bi-moon'"></i>
        {{ isDark ? 'Clair' : 'Sombre' }}
      </button>
      <div v-if="unreadCount > 0" class="mt-3 small text-muted text-center">
        {{ unreadCount }} message{{ unreadCount > 1 ? 's' : '' }} non lus
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, defineProps, toRefs, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { api, backendBase } from '@/utils/api'
import { computeAvatarInitials, normalizeAvatarUrl } from '@/utils/profile'

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
    return `${relative} • IP ${ip}`
  }
  return relative || (ip ? `IP ${ip}` : '')
})

const quickLinks = computed(() => [
  {
    to: '/dashboard/messages',
    label: 'Messages',
    hint: unreadCount.value > 0 ? `${unreadCount.value} non lus` : 'Flux s\u00e9curis\u00e9',
    icon: 'bi bi-chat-dots-fill',
  },
  {
    to: '/dashboard/contacts',
    label: 'Contacts',
    hint:
      pendingContacts.value > 0
        ? `${pendingContacts.value} demande${pendingContacts.value > 1 ? 's' : ''} en attente`
        : '\u00c9quipe & partenaires',
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
    hint: 'Sessions approuv\u00e9es',
    icon: 'bi bi-laptop',
  },
  {
    to: '/dashboard/settings',
    label: 'Param\u00e8tres',
    hint: 'S\u00e9curit\u00e9 & alertes',
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
  if (normalized === 'en reunion') return 'meeting'
  if (normalized === 'occupe') return 'busy'
  if (normalized === 'ne pas deranger') return 'dnd'
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

<style scoped>
.sidebar {
  width: clamp(240px, 20vw, 280px);
  min-width: 240px;
  position: sticky;
  top: 1.5rem;
  height: calc(100vh - 3rem);
  overflow-y: auto;
  padding: 1.4rem 1.2rem;
  border-right: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.35s ease, color 0.35s ease, border-color 0.35s ease, box-shadow 0.35s ease;
  box-shadow: 0 18px 38px rgba(15, 23, 42, 0.15);
  border-radius: 28px;
}

.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-thumb {
  background-color: rgba(108, 117, 125, 0.4);
  border-radius: 999px;
}

.sidebar-light {
  background: linear-gradient(180deg, #f9fbff 0%, #e7eeff 55%, #d9e6ff 100%);
  color: #1f2933;
  border-color: rgba(13, 110, 253, 0.08);
}

.sidebar-dark {
  background: radial-gradient(circle at 12% 10%, rgba(37, 99, 235, 0.28), transparent 60%),
    linear-gradient(180deg, #0d1322 0%, #081024 100%);
  color: #e5e7eb;
  border-color: rgba(255, 255, 255, 0.06);
}

.brand-link {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.9rem 0.65rem;
  border-radius: 20px;
  background: linear-gradient(160deg, rgba(13, 110, 253, 0.12), rgba(13, 110, 253, 0));
  box-shadow: 0 12px 24px rgba(13, 110, 253, 0.16);
  transition: transform 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
}

.brand-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 18px 32px rgba(13, 110, 253, 0.18);
  background: linear-gradient(160deg, rgba(13, 110, 253, 0.18), rgba(13, 110, 253, 0.04));
}

.sidebar-dark .brand-link {
  background: linear-gradient(160deg, rgba(59, 130, 246, 0.22), rgba(13, 110, 253, 0.06));
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.6);
}

.sidebar-dark .brand-link:hover {
  box-shadow: 0 18px 36px rgba(15, 23, 42, 0.65);
}

.sidebar-light .brand-link {
  background: linear-gradient(160deg, rgba(13, 110, 253, 0.1), rgba(13, 110, 253, 0.02));
}

.brand-link h4 {
  letter-spacing: 0.04em;
}

.brand-link .tagline {
  display: block;
  font-size: 0.75rem;
  margin-top: 0.1rem;
  opacity: 0.7;
}

.sidebar-profile {
  display: flex;
  align-items: center;
  gap: 0.95rem;
  padding: 0.85rem;
  border-radius: 16px;
  background-color: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(6px);
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.18);
  transition: background-color 0.3s ease, box-shadow 0.3s ease;
}

.sidebar-light .sidebar-profile {
  background-color: rgba(255, 255, 255, 0.94);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
}

.profile-avatar {
  flex-shrink: 0;
  width: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.profile-details {
  flex: 1;
  min-width: 0;
}

.profile-heading {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.35rem;
  width: 100%;
  margin-bottom: 0.35rem;
}

.profile-name {
  width: 100%;
  font-size: 1rem;
  font-weight: 600;
  color: #0f172a;
  word-break: normal;
  overflow-wrap: break-word;
}

.sidebar-dark .profile-name {
  color: #f8fafc;
}

.profile-status-line {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.35rem;
  font-size: 0.82rem;
  color: #0f172a;
  line-height: 1.25;
  margin: 0 0 0.2rem;
}

.sidebar-dark .profile-status-line {
  color: #e2e8f0;
}

.status-text {
  flex: 1;
  min-width: 0;
  word-break: break-word;
}

.profile-connection {
  margin: 0;
  font-size: 0.78rem;
  color: rgba(15, 23, 42, 0.7);
}

.sidebar-dark .profile-connection {
  color: rgba(226, 232, 240, 0.9);
}

.profile-connection.is-offline {
  color: #f97316;
}

.sidebar-dark .profile-connection.is-offline {
  color: #fdba74;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.status-dot.status-available {
  background: #22c55e;
}

.status-dot.status-away {
  background: #facc15;
}

.status-dot.status-meeting {
  background: #fb923c;
}

.status-dot.status-busy,
.status-dot.status-dnd {
  background: #f87171;
}

.status-dot.status-offline {
  background: #94a3b8;
}

.avatar-fallback {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  text-transform: uppercase;
}

.encryption-badge {
  background: rgba(59, 130, 246, 0.18);
  color: #bfdbfe;
  border-radius: 999px;
  font-size: 0.65rem;
  letter-spacing: 0.02em;
  padding: 0.35rem 0.55rem;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.sidebar-light .encryption-badge {
  background: rgba(13, 110, 253, 0.15);
  color: #0d6efd;
}

.sidebar-actions .btn {
  border-radius: 12px;
  padding: 0.55rem 0.85rem;
  font-weight: 600;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.sidebar-actions .btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 20px rgba(13, 110, 253, 0.2);
}

.sidebar .nav-link {
  color: inherit;
  display: flex;
  align-items: center;
  gap: 0.55rem;
  border-radius: 12px;
  padding: 0.52rem 0.7rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}

.sidebar .nav-link .badge {
  margin-left: auto;
}

.sidebar .nav-link:hover {
  background: rgba(13, 110, 253, 0.12);
  transform: translateX(3px);
  box-shadow: 0 8px 18px rgba(13, 110, 253, 0.18);
}

.sidebar-dark .nav-link {
  color: rgba(229, 231, 235, 0.85);
}

.sidebar-light .nav-link {
  color: rgba(15, 23, 42, 0.75);
}

.sidebar-dark .nav-link.active,
.sidebar-dark .nav-link.router-link-exact-active {
  background: rgba(59, 130, 246, 0.25);
  color: #f8fafc;
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.35), 0 10px 22px rgba(15, 23, 42, 0.28);
}

.sidebar-light .nav-link.active,
.sidebar-light .nav-link.router-link-exact-active {
  background: #0d6efd;
  color: #fff;
  box-shadow: 0 12px 24px rgba(13, 110, 253, 0.24);
}

.sidebar-section-title {
  text-transform: uppercase;
  font-size: 0.68rem;
  letter-spacing: 0.12em;
  color: rgba(148, 163, 184, 0.8);
  margin-bottom: 0.45rem;
}

.sidebar-light .sidebar-section-title {
  color: rgba(71, 85, 105, 0.9);
}

.sidebar-security {
  margin: 0;
  padding: 0;
}

.security-item {
  display: flex;
  align-items: center;
  padding: 0.55rem 0;
}

.quick-links-grid {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
}

.quick-link {
  border-radius: 16px;
  padding: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.8rem;
  text-decoration: none;
  color: inherit;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.sidebar-light .quick-link {
  background: rgba(255, 255, 255, 0.85);
  border-color: rgba(15, 23, 42, 0.08);
}

.quick-link:hover {
  transform: translateX(4px);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.2);
  border-color: rgba(59, 130, 246, 0.35);
}

.quick-link__icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
  background: rgba(59, 130, 246, 0.18);
  color: #60a5fa;
}

.quick-link__body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.quick-link__label {
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  line-height: 1.3;
  word-break: break-word;
}

.quick-link__badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.12);
  color: #0f172a;
  line-height: 1.1;
}

.sidebar-dark .quick-link__badge {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
}

.quick-link__badge--warning {
  background: rgba(249, 115, 22, 0.25);
  color: #f97316;
}

.sidebar-dark .quick-link__badge--warning {
  background: rgba(251, 191, 36, 0.25);
  color: #facc15;
}

.quick-link__hint {
  font-size: 0.8rem;
  color: rgba(148, 163, 184, 0.9);
  display: block;
  line-height: 1.25;
  white-space: normal;
}

.quick-link__chevron {
  font-size: 1.5rem;
  color: rgba(148, 163, 184, 0.9);
}

.sidebar-insights {
  border-radius: 20px;
  padding: 1.1rem;
  background: linear-gradient(145deg, rgba(15, 118, 243, 0.15), rgba(67, 56, 202, 0.3));
  color: #fff;
  box-shadow: 0 14px 32px rgba(15, 23, 42, 0.35);
}

.sidebar-light .sidebar-insights {
  color: #0f172a;
  background: linear-gradient(145deg, rgba(226, 232, 240, 0.9), rgba(191, 219, 254, 0.85));
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.1);
}

.insights-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.insights-eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.65rem;
  opacity: 0.8;
  margin-bottom: 0.15rem;
}

.insights-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
  gap: 0.9rem;
}

.insight-highlight {
  border-radius: 14px;
  padding: 0.85rem;
  background: rgba(15, 23, 42, 0.2);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.sidebar-light .insight-highlight {
  background: rgba(255, 255, 255, 0.92);
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.05);
}

.highlight-label {
  text-transform: uppercase;
  font-size: 0.7rem;
  letter-spacing: 0.12em;
  color: rgba(226, 232, 240, 0.85);
  margin-bottom: 0.3rem;
}

.sidebar-light .highlight-label {
  color: rgba(71, 85, 105, 0.85);
}

.highlight-value {
  font-size: 1.45rem;
  font-weight: 600;
  color: #fff;
  margin-bottom: 0.2rem;
}

.sidebar-light .highlight-value {
  color: #0f172a;
}

.insight-highlight small {
  font-size: 0.78rem;
  color: rgba(226, 232, 240, 0.8);
}

.sidebar-light .insight-highlight small {
  color: rgba(71, 85, 105, 0.85);
}

.insight-actions {
  display: flex;
  flex-direction: column;
  gap: 0.7rem;
}

.insight-action {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.85rem;
  border-radius: 16px;
  background: rgba(15, 23, 42, 0.32);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.05);
}

.sidebar-light .insight-action {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.05);
}

.insight-action__icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  color: #fff;
}

.insight-action__icon.variant-danger {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.insight-action__icon.variant-warning {
  background: linear-gradient(135deg, #f97316, #ea580c);
}

.insight-action__icon.variant-info {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
}

.insight-action__icon.variant-muted {
  background: linear-gradient(135deg, #94a3b8, #64748b);
}

.insight-action__icon.variant-success {
  background: linear-gradient(135deg, #22c55e, #16a34a);
}

.insight-action__body {
  flex: 1;
  min-width: 0;
}

.insight-action__title {
  font-weight: 600;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin: 0;
}

.sidebar-light .insight-action__title {
  color: #0f172a;
}

.insight-action__description {
  color: rgba(226, 232, 240, 0.82);
  line-height: 1.3;
}

.sidebar-light .insight-action__description {
  color: rgba(71, 85, 105, 0.85);
}

.insight-action__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.05rem 0.45rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.15);
  font-size: 0.7rem;
  letter-spacing: 0.05em;
}

.sidebar-light .insight-action__badge {
  background: rgba(15, 23, 42, 0.08);
  color: #0f172a;
}

.insight-activity {
  display: inline-flex;
  align-items: center;
  font-size: 0.85rem;
  background: rgba(15, 23, 42, 0.18);
  border-radius: 999px;
  padding: 0.4rem 0.85rem;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);
}

.sidebar-light .insight-activity {
  background: rgba(15, 23, 42, 0.06);
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.08);
}

.security-item .label {
  display: block;
  font-weight: 600;
}

.security-icon {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 0.85rem;
  font-size: 1.05rem;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.security-icon.info {
  background: rgba(59, 130, 246, 0.18);
  color: #60a5fa;
}

.security-icon.success {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.security-icon.warning {
  background: rgba(250, 204, 21, 0.2);
  color: #facc15;
}

.security-icon.muted {
  background: rgba(148, 163, 184, 0.2);
  color: rgba(148, 163, 184, 0.9);
}

.audit-card {
  display: flex;
  align-items: center;
  background: rgba(15, 23, 42, 0.15);
  border-radius: 14px;
  padding: 0.75rem;
  gap: 0.85rem;
  transition: background-color 0.3s ease;
}

.sidebar-light .audit-card {
  background: rgba(148, 163, 184, 0.18);
}

.audit-icon {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.18);
  color: #60a5fa;
  font-size: 1rem;
}

.manage-security {
  margin-top: 1rem;
  border: none;
  background: none;
  padding: 0;
  color: inherit;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
  transition: color 0.2s ease;
}

.manage-security:hover {
  color: #60a5fa;
}

.sidebar-light .manage-security:hover {
  color: #0d6efd;
}

.sidebar-footer {
  text-align: center;
}

.connection-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.4rem 0.85rem;
  border-radius: 999px;
  background: rgba(148, 163, 184, 0.18);
  font-size: 0.8rem;
  gap: 0.5rem;
}

.sidebar-light .connection-status {
  background: rgba(15, 23, 42, 0.08);
}

.status-indicator {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.theme-toggle {
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
  margin-top: 0.75rem;
  width: 100%;
}
</style>



