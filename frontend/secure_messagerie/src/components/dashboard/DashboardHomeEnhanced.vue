<!--
  ===== Component Header =====
  Component: DashboardHomeEnhanced
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Vue d'accueil du dashboard (stats, securite, contacts).
-->
<template>
  <div class="container py-4">
    <div v-if="loading && !overview" class="card border-0 shadow-sm loading-card">
      <div class="card-body text-center py-5">
        <div class="spinner-border text-primary mb-3" role="status"></div>
        <p class="text-muted mb-0">Chargement du tableau de bord securise...</p>
      </div>
    </div>

    <template v-else>
      <div v-if="error" class="status-banner mb-4">
        <div class="d-flex align-items-start gap-3 flex-wrap">
          <div class="status-icon">
            <i class="bi bi-shield-exclamation"></i>
          </div>
          <div class="flex-grow-1">
            <p class="mb-1 fw-semibold text-dark">Impossible de charger le tableau de bord</p>
            <p class="mb-0 text-muted small">{{ error }}</p>
          </div>
          <button class="btn btn-outline-primary btn-sm" :disabled="refreshing" @click="refreshOverview">
            <span v-if="refreshing" class="spinner-border spinner-border-sm me-1"></span>
            Réessayer
          </button>
        </div>
      </div>

      <div class="row g-4">
        <div class="col-12">
          <div class="hero card border-0 overflow-hidden animate__animated animate__fadeIn">
            <div class="hero-bg"></div>
            <div class="hero-content d-flex align-items-center flex-wrap gap-3">
              <img
                v-if="avatarUrl"
                :src="avatarUrl"
                alt="Avatar"
                class="avatar-hero"
                @error="onAvatarError"
              />
              <div v-else class="avatar-hero placeholder d-flex align-items-center justify-content-center">
                {{ heroInitials }}
              </div>
              <div class="flex-grow-1">
                <div class="text-white-50 small mb-1">{{ greeting }}</div>
                <h2 class="m-0 fw-bold text-white">Bienvenue, {{ pseudo }} !</h2>
                <div class="text-white-75 mt-1">
                  Messagerie sécurisée, simple et réactive pour votre équipe.
                </div>
              </div>
              <div class="hero-actions d-flex gap-2 flex-wrap">
                <router-link to="/dashboard/messages" class="btn btn-light btn-sm">
                  <i class="bi bi-chat-dots me-1"></i>
                  Ouvrir les messages
                </router-link>
                <router-link to="/dashboard/contacts" class="btn btn-outline-light btn-sm">
                  <i class="bi bi-person-plus me-1"></i>
                  Inviter un contact
                </router-link>
              </div>
            </div>
            <div class="hero-footer text-white-50 small d-flex align-items-center justify-content-between flex-wrap">
              <div>
                <i :class="apiOk ? 'bi bi-check-circle-fill text-success' : 'bi bi-x-circle-fill text-danger'"></i>
                <span class="ms-2">{{ apiOk ? 'API disponible' : 'API indisponible' }}</span>
              </div>
              <div v-if="lastRefreshLabel">
                Actualise {{ lastRefreshLabel }}
              </div>
            </div>
          </div>
        </div>

        <div class="col-12">
          <div class="row g-3">
            <div class="col-6 col-xl-3" v-for="tile in tiles" :key="tile.key">
              <div class="tile card h-100 text-decoration-none">
                <div class="card-body d-flex align-items-center gap-3">
                  <div :class="['icon-wrap', tile.iconClass]">
                    <i :class="tile.icon"></i>
                  </div>
                  <div>
                    <div class="tile-label">{{ tile.label }}</div>
                    <div class="tile-value">{{ tile.value }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="col-12" v-if="organization">
          <div
            class="card organization-highlight"
            :class="{ 'organization-highlight--admin': canManageOrganization }"
          >
            <div class="card-body d-flex flex-wrap align-items-center gap-3">
              <div class="flex-grow-1">
                <div class="text-muted small">Organisation</div>
                <h5 class="mb-1">{{ organization.name }}</h5>
                <div class="text-muted small">
                  {{ organization.member_count }} membres • {{ organization.admin_count }} administrateurs
                </div>
              </div>
              <div class="text-center">
                <div class="text-muted small">Votre rôle</div>
                <span class="badge" :class="organizationRoleBadgeClass">
                  {{ organizationRoleText(organization.membership.role) }}
                </span>
              </div>
              <router-link
                v-if="canManageOrganization"
                to="/dashboard/settings"
                class="btn btn-outline-primary btn-sm"
              >
                <i class="bi bi-gear me-1"></i>
                Gérer les administrateurs
              </router-link>
              <div v-else class="text-muted small">
                Contactez un administrateur pour modifier les accès.
              </div>
            </div>
          </div>
        </div>

        <div class="col-12 col-lg-8">
          <div class="card h-100">
            <div class="card-header bg-white d-flex align-items-center">
              <i class="bi bi-clock-history me-2 text-primary"></i>
              <strong>Dernières conversations</strong>
              <router-link to="/dashboard/messages" class="ms-auto small">
                Tout voir
              </router-link>
            </div>
            <div class="list-group list-group-flush">
              <div v-if="recentConversations.length === 0" class="p-3 text-muted small">
                Aucune conversation récemment active.
              </div>
              <button
                v-for="conversation in recentConversations"
                :key="conversation.id"
                type="button"
                class="list-group-item list-group-item-action d-flex align-items-start gap-3"
                @click="goToConversation(conversation.id)"
              >
                <div class="conversation-badge" :class="{ 'conversation-badge--unread': conversation.unread_count > 0 }">
                  <i class="bi bi-chat-dots"></i>
                </div>
                <div class="flex-grow-1">
                  <div class="d-flex align-items-center justify-content-between gap-2">
                    <div class="fw-semibold">
                      {{ conversation.title || 'Conversation' }}
                    </div>
                    <small class="text-muted">
                      {{ formatRelative(conversation.last_activity_at) }}
                    </small>
                  </div>
                  <div v-if="conversation.participants.length" class="text-muted small">
                    {{ conversation.participants.join(', ') }}
                  </div>
                  <div v-if="conversation.last_message_preview" class="preview text-muted small mt-1">
                    {{ conversation.last_message_preview }}
                  </div>
                </div>
                <span v-if="conversation.unread_count > 0" class="badge rounded-pill text-bg-primary">
                  {{ conversation.unread_count }}
                </span>
              </button>
            </div>
          </div>
        </div>

        <div class="col-12 col-lg-4">
          <div class="side-stack">
            <div class="card">
              <div class="card-header bg-white d-flex align-items-center">
                <i class="bi bi-shield-lock me-2 text-primary"></i>
                <strong>Profil à sécuriser</strong>
              </div>
              <div class="card-body">
                <div class="d-flex align-items-center gap-3 mb-3">
                  <span class="status-dot" :class="security.totp_enabled ? 'ok' : 'ko'"></span>
                  <div>
                    <div class="fw-semibold">Double authentification</div>
                    <div class="text-muted small">
                      {{ security.totp_enabled ? 'Activee' : 'Non activee' }}
                    </div>
                  </div>
                </div>
                <ul class="list-unstyled small mb-0">
                  <li>
                    <i :class="security.notification_login ? 'bi bi-bell-fill text-success' : 'bi bi-bell-slash text-muted'"></i>
                    <span class="ms-2">
                      Alertes connexion {{ security.notification_login ? 'actives' : 'inactives' }}
                    </span>
                  </li>
                  <li class="mt-1">
                    <i :class="security.has_recovery_codes ? 'bi bi-key-fill text-success' : 'bi bi-key text-muted'"></i>
                    <span class="ms-2">
                      Codes de récupération {{ security.has_recovery_codes ? 'disponibles' : 'manquants' }}
                    </span>
                  </li>
                  <li v-if="security.last_totp_failure_at" class="mt-1 text-muted">
                    Dernier échec MFA {{ formatRelative(security.last_totp_failure_at) }}
                  </li>
                </ul>
              </div>
            </div>
            <div class="card">
              <div class="card-header bg-white d-flex align-items-center">
                <i class="bi bi-list-check me-2 text-primary"></i>
                <strong>Actions recommandees</strong>
              </div>
              <div class="card-body">
                <p v-if="recommendations.length === 0" class="text-muted small mb-0">
                  Aucun point critique détecté. Continuez à surveiller vos sessions.
                </p>
                <ol v-else class="recommendations list-group list-group-numbered">
                  <li v-for="item in recommendations" :key="item" class="list-group-item small">
                    {{ item }}
                  </li>
                </ol>
              </div>
            </div>

            <div class="card">
              <div class="card-header bg-white d-flex align-items-center">
                <i class="bi bi-activity me-2 text-primary"></i>
                <strong>Etat du compte</strong>
              </div>
              <div class="card-body small text-muted">
                <div class="d-flex align-items-center justify-content-between mb-2">
                  <span>Appareils</span>
                  <span>
                    {{ stats.devices_total }} total
                    <span v-if="stats.devices_at_risk > 0" class="text-danger">
                      · {{ stats.devices_at_risk }} a risque
                    </span>
                  </span>
                </div>
                <div class="d-flex align-items-center justify-content-between">
                  <span>Dernier appareil vu</span>
                  <span>{{ lastDeviceSeenLabel }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, backendBase } from '@/utils/api'
import { computeAvatarInitials, normalizeAvatarUrl } from '@/utils/profile'

// ===== Navigation =====
const router = useRouter()

// ===== Etats reactivs principaux =====
const loading = ref(true)
const refreshing = ref(false)
const error = ref('')
const apiOk = ref(false)

const overview = ref(null)

// ===== Infos utilisateur pour le hero =====
const pseudo = ref(localStorage.getItem('pseudo') || 'Utilisateur')
const avatarUrl = ref(normalizeAvatarUrl(localStorage.getItem('avatar_url'), { baseUrl: backendBase }))
const heroInitials = computed(() =>
  computeAvatarInitials({
    displayName: pseudo.value,
    fallback: 'C',
  }),
)
const greeting = ref('Bonjour')

// ===== Valeurs par defaut pour eviter les undefined en rendu =====
const defaultStats = {
  unread_messages: 0,
  conversations: 0,
  contacts_total: 0,
  contacts_pending: 0,
  devices_total: 0,
  devices_at_risk: 0,
  last_device_seen_at: null,
}

const defaultSecurity = {
  totp_enabled: false,
  notification_login: false,
  has_recovery_codes: false,
  last_totp_failure_at: null,
  recommendations: [],
}

const stats = computed(() => overview.value?.stats ?? defaultStats)
const security = computed(() => overview.value?.security ?? defaultSecurity)
const recentConversations = computed(() => overview.value?.recent_conversations ?? [])
const recommendations = computed(() => security.value.recommendations ?? [])
const organization = computed(() => overview.value?.organization ?? null)
const organizationMembership = computed(() => organization.value?.membership ?? null)
const canManageOrganization = computed(() => Boolean(organizationMembership.value?.can_manage_admins))
const organizationRoleBadgeClass = computed(() => badgeClassForRole(organizationMembership.value?.role))

// ===== Cartes indicateurs principales =====
const tiles = computed(() => {
  const snapshot = stats.value
  return [
    {
      key: 'unread',
      label: 'Non lus',
      value: snapshot.unread_messages,
      icon: 'bi bi-envelope-open',
      iconClass: 'bg-primary-subtle text-primary',
    },
    {
      key: 'conversations',
      label: 'Conversations',
      value: snapshot.conversations,
      icon: 'bi bi-chat',
      iconClass: 'bg-info-subtle text-info',
    },
    {
      key: 'contacts',
      label: 'Contacts',
      value: snapshot.contacts_total,
      icon: 'bi bi-people',
      iconClass: 'bg-success-subtle text-success',
    },
    {
      key: 'invitations',
      label: 'Invitations',
      value: snapshot.contacts_pending,
      icon: 'bi bi-person-plus',
      iconClass: 'bg-warning-subtle text-warning',
    },
  ]
})

const lastRefreshLabel = computed(() => {
  const ts = overview.value?.generated_at
  return ts ? formatRelative(ts) : ''
})

const lastDeviceSeenLabel = computed(() => {
  const ts = stats.value.last_device_seen_at
  if (!ts) return 'Aucun'
  const relative = formatRelative(ts)
  const absolute = formatDateTime(ts)
  return relative ? `${relative} (${absolute})` : absolute
})

onMounted(async () => {
  greeting.value = computeGreeting()
  if (typeof window !== 'undefined') {
    window.addEventListener('cova:profile-update', handleProfileUpdate)
  }
  await fetchOverview()
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('cova:profile-update', handleProfileUpdate)
  }
})

// ===== Rappel principal vers l'API dashboard =====
async function fetchOverview(options = {}) {
  const silent = options.silent ?? false
  if (silent) {
    refreshing.value = true
  } else {
    loading.value = true
  }
  error.value = ''
  try {
    const { data } = await api.get('/me/overview')
    overview.value = data
    apiOk.value = true

    const nextPseudo = resolvePseudo(data.profile)
    if (nextPseudo) {
      pseudo.value = nextPseudo
      try {
        localStorage.setItem('pseudo', nextPseudo)
      } catch {}
    }
    if (Object.prototype.hasOwnProperty.call(data.profile || {}, 'avatar_url')) {
      const normalized = normalizeAvatarUrl(data.profile.avatar_url, {
        baseUrl: backendBase,
        cacheBust: true,
      })
      avatarUrl.value = normalized
      try {
        if (normalized) {
          localStorage.setItem('avatar_url', normalized)
        } else {
          localStorage.removeItem('avatar_url')
        }
      } catch {}
    }
  } catch (err) {
    apiOk.value = false
    if (err.response?.status === 401 || err.response?.status === 403) {
      return
    }
    error.value = extractErrorMessage(err) || "Impossible de charger l'accueil sécurisé. Veuillez vérifier votre connexion puis réessayer."
  } finally {
    if (silent) {
      refreshing.value = false
    } else {
      loading.value = false
    }
  }
}

async function refreshOverview() {
  await fetchOverview({ silent: Boolean(overview.value) })
}

function computeGreeting() {
  const hour = new Date().getHours()
  if (hour < 5) return 'Bonsoir'
  if (hour < 12) return 'Bonjour'
  if (hour < 18) return 'Bon après-midi'
  return 'Bonsoir'
}

function resolvePseudo(profile) {
  if (!profile) return null
  const displayName = (profile.display_name || '').trim()
  if (displayName) return displayName
  if (profile.email) {
    const localPart = profile.email.split('@')[0]
    return localPart || null
  }
  return null
}

function goToConversation(id) {
  router.push({ path: '/dashboard/messages', query: { conversation: id } })
}

// ===== Maj du hero en cas de changement de profil global =====
function handleProfileUpdate(event) {
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
}

function onAvatarError() {
  avatarUrl.value = null
  try {
    localStorage.removeItem('avatar_url')
  } catch {}
}

function organizationRoleText(role) {
  if (role === 'owner') return 'Propriétaire'
  if (role === 'admin') return 'Administrateur'
  if (role === 'auditor') return 'Auditeur'
  return 'Membre'
}

function badgeClassForRole(role) {
  if (role === 'owner') return 'bg-dark text-white'
  if (role === 'admin') return 'bg-primary-subtle text-primary'
  if (role === 'auditor') return 'bg-info-subtle text-info'
  return 'bg-light text-dark'
}

function formatRelative(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const diffSeconds = Math.round((date.getTime() - Date.now()) / 1000)
  const absSeconds = Math.abs(diffSeconds)
  const direction = diffSeconds < 0 ? 'il y a' : 'dans'

  const ranges = [
    { threshold: 60, divisor: 1, label: 'seconde' },
    { threshold: 3600, divisor: 60, label: 'minute' },
    { threshold: 86400, divisor: 3600, label: 'heure' },
    { threshold: 604800, divisor: 86400, label: 'jour' },
    { threshold: 2629800, divisor: 604800, label: 'semaine' },
    { threshold: 31557600, divisor: 2629800, label: 'mois' },
  ]

  for (const range of ranges) {
    if (absSeconds < range.threshold) {
      const valueRounded = Math.max(1, Math.round(diffSeconds / range.divisor))
      const plural = Math.abs(valueRounded) > 1 ? 's' : ''
      return `${direction} ${Math.abs(valueRounded)} ${range.label}${plural}`
    }
  }

  const years = Math.round(diffSeconds / 31557600)
  const plural = Math.abs(years) > 1 ? 's' : ''
  return `${direction} ${Math.abs(years)} an${plural}`
}

function formatDateTime(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const pad = (input) => String(input).padStart(2, '0')
  const day = pad(date.getDate())
  const month = pad(date.getMonth() + 1)
  const year = date.getFullYear()
  const hours = pad(date.getHours())
  const minutes = pad(date.getMinutes())
  return `${day}/${month}/${year} ${hours}h${minutes}`
}

function extractErrorMessage(err) {
  if (!err) return ''
  if (typeof err === 'string') return err
  const response = err.response?.data
  const detail =
    (typeof response?.detail === 'string' && response.detail) ||
    response?.message ||
    response?.error ||
    err.message
  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim()
  }
  return ''
}
</script>

<!-- ===== Styles de la page d'accueil dashboard ===== -->
<style scoped>
.loading-card {
  max-width: 480px;
  margin: 0 auto;
}

.hero {
  position: relative;
  border-radius: 18px;
}

.hero-bg {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, #2157d3 0%, #0d6efd 60%, #57a0ff 100%);
  opacity: 0.95;
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: 24px;
}

.hero-footer {
  position: relative;
  z-index: 1;
  padding: 12px 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.15);
}

.hero-actions .btn {
  min-width: 170px;
}

.avatar-hero {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.avatar-hero.placeholder {
  background: rgba(255, 255, 255, 0.15);
  font-size: 1.6rem;
  color: #fff;
  font-weight: 600;
  text-transform: uppercase;
}

.text-white-75 {
  color: rgba(255, 255, 255, 0.85);
}

.tile {
  border: 1px solid #e7ecf7;
  border-radius: 16px;
  box-shadow: 0 8px 22px rgba(13, 110, 253, 0.08);
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}

.tile:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(13, 110, 253, 0.12);
}

.icon-wrap {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
}

.tile-label {
  color: #6b789a;
  font-size: 0.9rem;
}

.tile-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: #1b2b59;
}

.organization-highlight {
  border-left: 4px solid #94a3b8;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.organization-highlight--admin {
  border-left-color: #0d6efd;
  box-shadow: 0 8px 24px rgba(13, 110, 253, 0.15);
}
.status-banner {
  border-radius: 16px;
  padding: 1rem 1.25rem;
  background: #fff7e6;
  border: 1px solid #ffe0b3;
  box-shadow: 0 8px 20px rgba(255, 165, 0, 0.15);
}

.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  background: rgba(255, 193, 7, 0.2);
  display: grid;
  place-items: center;
  font-size: 1.4rem;
  color: #e77717;
}

.conversation-badge {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: #e7ecf7;
  color: #0d6efd;
}

.conversation-badge--unread {
  background: rgba(13, 110, 253, 0.18);
}

.preview {
  max-height: 2.8em;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
}

.side-stack {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.recommendations .list-group-item {
  border: none;
  padding-left: 0;
  padding-right: 0;
  background: transparent;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 0 0 6px rgba(25, 135, 84, 0.15);
}

.status-dot.ko {
  background: #dc3545;
  box-shadow: 0 0 0 6px rgba(220, 53, 69, 0.15);
}

.status-dot.ok {
  background: #198754;
}

@media (max-width: 992px) {
  .hero-content {
    padding: 20px;
  }

  .hero-actions .btn {
    min-width: 0;
  }

  .side-stack {
    flex-direction: row;
    flex-wrap: wrap;
  }

  .side-stack .card {
    flex: 1 1 280px;
  }
}

@media (max-width: 576px) {
  .hero-actions {
    width: 100%;
  }

  .hero-actions .btn {
    flex: 1 1 auto;
  }
}
</style>
