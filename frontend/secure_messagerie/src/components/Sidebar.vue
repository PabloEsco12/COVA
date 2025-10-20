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
        <div class="d-flex align-items-center justify-content-between">
          <h6 class="mb-0">{{ pseudo }}</h6>
          <span class="badge encryption-badge">
            <i class="bi bi-lock-fill me-1"></i>
            Chiffré
          </span>
        </div>
        <small class="text-muted">{{ isOnline ? 'Connexion sécurisée' : 'Hors ligne' }}</small>
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

    <section class="sidebar-section">
      <p class="sidebar-section-title">Navigation</p>
      <ul class="nav nav-pills flex-column">
        <li class="nav-item">
          <router-link to="/dashboard" class="nav-link" exact-active-class="active">
            <i class="bi bi-house me-2"></i> Accueil
          </router-link>
        </li>
        <li>
          <router-link to="/dashboard/messages" class="nav-link" active-class="active">
            <i class="bi bi-chat-dots me-2"></i> Messages
            <span v-if="unreadCount > 0" class="badge bg-danger ms-auto">{{ unreadCount }}</span>
          </router-link>
        </li>
        <li>
          <router-link to="/dashboard/contacts" class="nav-link" active-class="active">
            <i class="bi bi-people me-2"></i> Contacts
          </router-link>
        </li>
        <li>
          <router-link to="/dashboard/invitations" class="nav-link" active-class="active">
            <i class="bi bi-person-plus me-2"></i> Invitations
          </router-link>
        </li>
        <li>
          <router-link to="/dashboard/devices" class="nav-link" active-class="active">
            <i class="bi bi-phone me-2"></i> Appareils
          </router-link>
        </li>
        <li>
          <router-link to="/dashboard/settings" class="nav-link" active-class="active">
            <i class="bi bi-gear me-2"></i> Paramètres
          </router-link>
        </li>
      </ul>
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
import { ref, onMounted, onBeforeUnmount, defineProps, toRefs, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api, backendBase } from '@/utils/api'
import { io } from 'socket.io-client'

const props = defineProps({
  isDark: Boolean
})

const { isDark } = toRefs(props)
const router = useRouter()

const userId = Number(localStorage.getItem('user_id') || 0)
const unreadCount = ref(0)
const unreadByConversation = ref({})
const activeConversationId = ref(null)
const socketRef = ref(null)
const conversationIds = ref([])
const joinedRooms = new Set()
const pseudo = ref('Utilisateur')
const avatarUrl = ref(null)
const isOnline = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
const securitySettings = ref({
  totpEnabled: false,
  notificationLogin: false
})
const lastAuditLog = ref(null)

const initials = computed(() => (pseudo.value ? pseudo.value.charAt(0).toUpperCase() : 'U'))
const lastAuditText = computed(() => {
  if (!lastAuditLog.value) return ''
  const { timestamp, ip } = lastAuditLog.value
  const relative = formatRelativeTime(timestamp)
  if (relative && ip) {
    return `${relative} • IP ${ip}`
  }
  return relative || (ip ? `IP ${ip}` : '')
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

function setUnreadMap(map) {
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
      setUnreadMap(raw)
    } catch {
      setUnreadMap({})
    }
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

function handleSocketMessage(payload) {
  if (!payload) return
  const convId = Number(payload.conv_id)
  if (!convId) return
  const sender = Number(payload.sender_id ?? payload.user_id ?? 0)
  if (sender && userId && sender === userId) return
  if (convId === activeConversationId.value) return
  incrementUnread(convId)
}

function handleMessageRead(payload) {
  if (!payload) return
  const reader = Number(payload.user_id ?? payload.id_user ?? 0)
  if (reader && userId && reader !== userId) return
  const convId = Number(payload.conv_id)
  if (!convId) return
  clearUnread(convId)
}

function ensureSocketConnected() {
  if (socketRef.value) return
  try {
    socketRef.value = io(backendBase, {
      transports: ['websocket'],
      auth: { token: localStorage.getItem('access_token') },
    })
    socketRef.value.on('connect', () => {
      joinedRooms.clear()
      joinKnownRooms()
    })
    socketRef.value.on('disconnect', () => {
      joinedRooms.clear()
    })
    socketRef.value.on('message_created', handleSocketMessage)
    socketRef.value.on('new_message', handleSocketMessage)
    socketRef.value.on('message_read', handleMessageRead)
  } catch (error) {
    socketRef.value = null
  }
}

function joinKnownRooms() {
  if (!socketRef.value) return
  for (const id of conversationIds.value || []) {
    const convId = Number(id)
    if (!convId || joinedRooms.has(convId)) continue
    socketRef.value.emit('join_conversation', { conv_id: convId })
    joinedRooms.add(convId)
  }
}

async function loadConversations() {
  try {
    const res = await api.get(`/conversations/`)
    const ids = (res.data || [])
      .map(item => Number(item?.id ?? item?.id_conv ?? 0))
      .filter(id => Number.isFinite(id) && id > 0)
    conversationIds.value = ids
    joinKnownRooms()
  } catch {
    conversationIds.value = []
  }
}

onMounted(async () => {
  pseudo.value = localStorage.getItem('pseudo') || 'Utilisateur'
  avatarUrl.value = localStorage.getItem('avatar_url') || null

  if (typeof window !== 'undefined') {
    window.addEventListener('online', updateNetworkStatus)
    window.addEventListener('offline', updateNetworkStatus)
    window.addEventListener('cova:unread', handleUnreadEvent)
    window.addEventListener('cova:active-conversation', handleActiveConversationEvent)
  }

  await loadUnreadSummary()

  const token = localStorage.getItem('access_token')
  if (!token) {
    return
  }

  ensureSocketConnected()
  await loadConversations()

  try {
    const profileRes = await api.get(`/me`)
    if (profileRes.data?.pseudo) {
      pseudo.value = profileRes.data.pseudo
      localStorage.setItem('pseudo', profileRes.data.pseudo)
    }
    const apiAvatar =
      profileRes.data?.avatar_url ||
      (profileRes.data?.avatar ? `${backendBase}/static/avatars/${profileRes.data.avatar}` : null)
    if (apiAvatar) {
      avatarUrl.value = apiAvatar
      localStorage.setItem('avatar_url', apiAvatar)
    }
  } catch (e) {
    // ignore
  }

  try {
    const securityRes = await api.get(`/me/security`)
    securitySettings.value = {
      totpEnabled: !!securityRes.data?.totp_enabled,
      notificationLogin: !!securityRes.data?.notification_login
    }
  } catch (e) {
    securitySettings.value = {
      totpEnabled: false,
      notificationLogin: false
    }
  }

  try {
    const auditRes = await api.get(`/me/audit`)
    if (Array.isArray(auditRes.data) && auditRes.data.length > 0) {
      lastAuditLog.value = auditRes.data[0]
    }
  } catch (e) {
    lastAuditLog.value = null
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('online', updateNetworkStatus)
    window.removeEventListener('offline', updateNetworkStatus)
    window.removeEventListener('cova:unread', handleUnreadEvent)
    window.removeEventListener('cova:active-conversation', handleActiveConversationEvent)
  }
  if (socketRef.value) {
    try {
      socketRef.value.disconnect()
    } catch {}
    socketRef.value = null
  }
  joinedRooms.clear()
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

<style scoped src="../styles/components/Sidebar.css"></style>
