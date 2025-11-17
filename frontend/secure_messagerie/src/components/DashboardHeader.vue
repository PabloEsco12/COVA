<template>
  <header
    :class="[
      'd-flex align-items-center justify-content-between px-4 py-2 shadow-sm header-bar',
      isDark ? 'header-bar-dark text-light' : 'bg-white',
    ]"
  >
    <div>
      <span class="fw-bold fs-5">Bienvenue {{ pseudo }} sur COVA&nbsp;!</span>
    </div>
    <div class="d-flex align-items-center">
      <div class="avatar-wrapper me-2">
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
      <span class="me-3">{{ pseudo }}</span>
      <button class="btn btn-outline-danger btn-sm" @click="handleLogout">Déconnexion</button>
    </div>
    <button
      @click="emit('toggle-dark')"
      :class="['btn ms-2 theme-toggle', isDark ? 'btn-outline-light' : 'btn-outline-secondary']"
      title="Activer/désactiver le mode sombre"
    >
      <i :class="isDark ? 'bi bi-moon-fill' : 'bi bi-brightness-high-fill'"></i>
    </button>
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
const avatarInitials = computed(() =>
  computeAvatarInitials({
    displayName: pseudo.value,
    fallback: 'C',
  }),
)

onMounted(async () => {
  pseudo.value = localStorage.getItem('pseudo') || 'Utilisateur'
  avatarUrl.value = normalizeAvatarUrl(localStorage.getItem('avatar_url'), { baseUrl: backendBase })
  if (typeof window !== 'undefined') {
    window.addEventListener('cova:profile-update', handleProfileUpdate)
  }

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
  if (typeof window !== 'undefined') {
    window.removeEventListener('cova:profile-update', handleProfileUpdate)
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
</script>

<style scoped>
.theme-toggle {
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}
.header-bar {
  transition: background-color 0.3s ease, color 0.3s ease, box-shadow 0.3s ease;
}
.header-bar-dark {
  background: rgba(22, 27, 34, 0.96);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.4);
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
</style>
