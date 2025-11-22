<template>
  <div class="container py-4">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="card p-5 shadow-lg text-center animate__animated animate__fadeIn">
          <h2 class="mb-2 display-5 fw-bold">Bienvenue {{ pseudo }} ??</h2>
          <div class="mb-3">
            <img v-if="avatarUrl" :src="avatarUrl" alt="Avatar" class="avatar-lg" @error="onAvatarError" />
            <div v-else class="avatar-lg avatar-placeholder">{{ avatarInitials }}</div>
          </div>
          <p class="lead mb-4">
            Messagerie sécurisée, simple et rapide.<br />
            Retrouvez vos messages, contacts et notifications ici.
          </p>
          <img src="@/assets/logo_COVA.png" alt="Logo COVA" style="width:80px; margin-bottom:20px;" />
          <div class="row mt-3">
            <div class="col-6 col-md-3 mb-3">
              <router-link to="/dashboard/messages" class="btn btn-primary w-100">
                <i class="bi bi-chat-dots me-1"></i> Messages
              </router-link>
            </div>
            <div class="col-6 col-md-3 mb-3">
              <router-link to="/dashboard/contacts" class="btn btn-outline-secondary w-100">
                <i class="bi bi-people"></i> Contacts
              </router-link>
            </div>
            <div class="col-6 col-md-3 mb-3">
              <router-link to="/dashboard/devices" class="btn btn-outline-secondary w-100">
                <i class="bi bi-phone"></i> Appareils
              </router-link>
            </div>
            <div class="col-6 col-md-3 mb-3">
              <router-link to="/dashboard/settings" class="btn btn-outline-secondary w-100">
                <i class="bi bi-gear"></i> Paramètres
              </router-link>
            </div>
          </div>
          <div class="mt-4 text-muted small">
            Statut API :
            <span :class="apiOk ? 'text-success' : 'text-danger'">
              <i :class="apiOk ? 'bi bi-circle-fill' : 'bi bi-x-circle-fill'"></i>
              {{ apiOk ? 'Connecté' : 'Hors ligne' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { api, backendBase } from '@/utils/api'
import { computeAvatarInitials, normalizeAvatarUrl } from '@/utils/profile'

const apiOk = ref(false)
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

  try {
    await api.get('/ping')
    apiOk.value = true
  } catch (e) {
    apiOk.value = false
  }

  const token = localStorage.getItem('access_token')
  if (token) {
    try {
      const res = await api.get('/me/profile')
      if (res.data?.display_name) {
        pseudo.value = res.data.display_name
        localStorage.setItem('pseudo', res.data.display_name)
      }
      if (Object.prototype.hasOwnProperty.call(res.data, 'avatar_url')) {
        const normalized = normalizeAvatarUrl(res.data.avatar_url, {
          baseUrl: backendBase,
          cacheBust: true,
        })
        avatarUrl.value = normalized
        if (normalized) {
          localStorage.setItem('avatar_url', normalized)
        } else {
          localStorage.removeItem('avatar_url')
        }
      }
    } catch (e) {
      // ignore
    }
  }
})

onBeforeUnmount(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('cova:profile-update', handleProfileUpdate)
  }
})

function onAvatarError() {
  try { localStorage.removeItem('avatar_url') } catch {}
  avatarUrl.value = null
}

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
</script>

<style scoped>
.avatar-lg {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 2px 8px #0002;
}
.avatar-placeholder {
  background: linear-gradient(135deg, #0d6efd, #6f42c1);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  text-transform: uppercase;
}
</style>
