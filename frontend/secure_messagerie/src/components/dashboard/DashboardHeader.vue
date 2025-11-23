<template>
  <header
    :class="[
      'header-shell d-flex align-items-center justify-content-between px-4 py-3',
      isDark ? 'header-bar-dark text-light' : 'header-bar-light',
    ]"
  >
    <div class="header-title">
      <span class="fw-bold fs-5 mb-0">Bienvenue {{ pseudo }} sur COVA&nbsp;!</span>
      <small class="text-muted d-none d-md-block">Espace sécurisé et collaboratif</small>
    </div>
    <div class="header-identity">
      <div class="avatar-wrapper">
        <img
          v-if="avatarUrl"
          :src="avatarUrl"
          alt="Avatar"
          class="rounded-circle"
          width="40"
          height="40"
          @error="onAvatarError"
        />
        <div v-else class="avatar-fallback">{{ avatarInitials }}</div>
      </div>
      <span class="user-name">{{ pseudo }}</span>
    </div>
    <div class="header-actions">
      <div class="chip" :class="isOnline ? 'chip-ok' : 'chip-off'">
        <i :class="isOnline ? 'bi bi-shield-check' : 'bi bi-wifi-off'"></i>
        <span>{{ isOnline ? 'Canal sécurisé' : 'Hors ligne' }}</span>
      </div>
      <div class="chip chip-muted">
        <i class="bi bi-clock-history"></i>
        <span>{{ formattedTime }}</span>
      </div>
      <button
        @click="emit('toggle-dark')"
        :class="['btn theme-toggle', isDark ? 'btn-outline-light' : 'btn-outline-secondary']"
        title="Activer/désactiver le mode sombre"
      >
        <i :class="isDark ? 'bi bi-moon-fill' : 'bi bi-brightness-high-fill'"></i>
      </button>
      <button class="btn btn-outline-danger btn-sm" @click="handleLogout">Déconnexion</button>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, defineProps, defineEmits, toRefs, computed } from 'vue'
import { api, backendBase } from '@/utils/api'
import { logout as revokeSession } from '@/services/auth'
import { computeAvatarInitials, normalizeAvatarUrl } from '@/utils/profile'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false,
  },
})

const { isDark } = toRefs(props)
const emit = defineEmits(['toggle-dark'])

const pseudo = ref('Utilisateur')
const avatarUrl = ref(normalizeAvatarUrl(localStorage.getItem('avatar_url'), { baseUrl: backendBase }))
const isOnline = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)
const nowClock = ref(new Date())
const avatarInitials = computed(() =>
  computeAvatarInitials({
    displayName: pseudo.value,
    fallback: 'C',
  }),
)
const formattedTime = computed(() =>
  nowClock.value.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
)
let clockTimer = null

onMounted(async () => {
  pseudo.value = localStorage.getItem('pseudo') || 'Utilisateur'
  avatarUrl.value = normalizeAvatarUrl(localStorage.getItem('avatar_url'), { baseUrl: backendBase })
  if (typeof window !== 'undefined') {
    window.addEventListener('cova:profile-update', handleProfileUpdate)
    window.addEventListener('online', updateNetworkStatus)
    window.addEventListener('offline', updateNetworkStatus)
  }
  clockTimer = setInterval(() => {
    nowClock.value = new Date()
  }, 60000)

  const token = localStorage.getItem('access_token')
  if (!token) return
  try {
    const res = await api.get('/me')
    if (res.data?.pseudo) {
      pseudo.value = res.data.pseudo
      localStorage.setItem('pseudo', res.data.pseudo)
    }
    const apiAvatar = normalizeAvatarUrl(
      res.data?.avatar_url || (res.data?.avatar ? `/static/avatars/${res.data.avatar}` : null),
      { baseUrl: backendBase },
    )
    if (apiAvatar) {
      avatarUrl.value = apiAvatar
      localStorage.setItem('avatar_url', apiAvatar)
    } else {
      avatarUrl.value = null
      localStorage.removeItem('avatar_url')
    }
  } catch {
    /* ignore fetch errors */
  }
})

onBeforeUnmount(() => {
  if (clockTimer) {
    clearInterval(clockTimer)
    clockTimer = null
  }
  if (typeof window !== 'undefined') {
    window.removeEventListener('cova:profile-update', handleProfileUpdate)
    window.removeEventListener('online', updateNetworkStatus)
    window.removeEventListener('offline', updateNetworkStatus)
  }
})

async function handleLogout() {
  try {
    await revokeSession()
  } catch {
    /* ignore */
  } finally {
    window.location.href = '/login'
  }
}

function onAvatarError() {
  avatarUrl.value = null
  try {
    localStorage.removeItem('avatar_url')
  } catch {}
}

function handleProfileUpdate(event) {
  const payload = event?.detail || {}
  if (Object.prototype.hasOwnProperty.call(payload, 'display_name')) {
    const next = (payload.display_name || '').trim() || 'Utilisateur'
    pseudo.value = next
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

function updateNetworkStatus() {
  if (typeof navigator !== 'undefined') {
    isOnline.value = navigator.onLine
  }
}
</script>

<style scoped>
.theme-toggle {
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
  width: 36px;
  height: 36px;
  padding: 0;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
}
.header-shell {
  transition: background-color 0.3s ease, color 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.06);
  gap: 0.75rem;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.12);
  flex-wrap: wrap;
  align-items: center;
}
.header-bar-light {
  background: #f9fbff;
  color: #0f172a;
}
.header-bar-dark {
  background: linear-gradient(135deg, #161c27 0%, #0f1625 100%);
  border-color: rgba(255, 255, 255, 0.06);
  color: #e5e7eb;
  box-shadow: 0 10px 26px rgba(0, 0, 0, 0.5);
}
.avatar-wrapper {
  width: 40px;
  height: 40px;
}
.avatar-wrapper img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.avatar-fallback {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: linear-gradient(135deg, #0d6efd, #6610f2);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  text-transform: uppercase;
}

.header-bar-dark .btn-outline-danger {
  color: #f8d7da;
  border-color: rgba(248, 215, 218, 0.6);
}

.header-bar-dark .btn-outline-danger:hover {
  background: rgba(248, 215, 218, 0.1);
}

.header-bar .btn-outline-secondary,
.header-bar .btn-outline-light {
  border-width: 1px;
}

.header-title {
  flex: 1;
  min-width: 220px;
}

.header-identity {
  flex: 1;
  min-width: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.header-actions {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  flex-wrap: wrap;
  justify-content: flex-end;
  flex: 1;
}

.user-name {
  font-weight: 600;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  font-size: 0.85rem;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: rgba(255, 255, 255, 0.8);
  color: #0f172a;
}

.chip i {
  font-size: 1rem;
}

.chip-muted {
  background: rgba(15, 23, 42, 0.04);
  color: #334155;
}

.chip-ok {
  background: rgba(16, 185, 129, 0.12);
  color: #0f766e;
  border-color: rgba(16, 185, 129, 0.3);
}

.chip-off {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
  border-color: rgba(239, 68, 68, 0.3);
}

.header-bar-dark .chip {
  background: rgba(255, 255, 255, 0.08);
  color: #e5e7eb;
  border-color: rgba(255, 255, 255, 0.12);
}

.header-bar-dark .chip-muted {
  background: rgba(255, 255, 255, 0.06);
  color: #cbd5e1;
}

.header-bar-dark .chip-ok {
  background: rgba(74, 222, 128, 0.14);
  color: #bbf7d0;
  border-color: rgba(74, 222, 128, 0.3);
}

.header-bar-dark .chip-off {
  background: rgba(248, 113, 113, 0.18);
  color: #fecdd3;
  border-color: rgba(248, 113, 113, 0.35);
}
</style>
