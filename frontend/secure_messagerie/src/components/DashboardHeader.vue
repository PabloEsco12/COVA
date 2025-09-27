<template>
  <header
    :class="[
      'd-flex align-items-center justify-content-between px-4 py-2 shadow-sm header-bar',
      isDark ? 'header-bar-dark text-light' : 'bg-white'
    ]"
  >
    <div>
      <span class="fw-bold fs-5">Bienvenue {{ pseudo }} sur COVA&nbsp;!</span>
    </div>
    <div class="d-flex align-items-center">
      <img v-if="avatarUrl" :src="avatarUrl" alt="Avatar" class="rounded-circle me-2" width="40" height="40" @error="onAvatarError" />
      <span class="me-3">{{ pseudo }}</span>
      <button class="btn btn-outline-danger btn-sm" @click="logout">Déconnexion</button>
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
import { ref, onMounted, defineProps, defineEmits, toRefs } from 'vue'
import axios from 'axios'

const props = defineProps({
  isDark: {
    type: Boolean,
    default: false
  }
})

const { isDark } = toRefs(props)
const emit = defineEmits(['toggle-dark'])

const pseudo = ref('')
const avatarUrl = ref(null)
const backendBase = (import.meta.env.VITE_API_URL || '').replace(/\/api\/?$/, '') || 'http://localhost:5000'

onMounted(async () => {
  // Lecture immédiate depuis le storage pour un rendu rapide
  pseudo.value = localStorage.getItem('pseudo') || 'Utilisateur'
  avatarUrl.value = localStorage.getItem('avatar_url') || null

  // Rafraîchir depuis l'API pour garantir la persistance
  const token = localStorage.getItem('access_token')
  if (token) {
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_URL}/me`, {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.data?.pseudo) {
        pseudo.value = res.data.pseudo
        localStorage.setItem('pseudo', res.data.pseudo)
      }
      const apiAvatar = res.data?.avatar_url || (res.data?.avatar ? `${backendBase}/static/avatars/${res.data.avatar}` : null)
      if (apiAvatar) {
        avatarUrl.value = apiAvatar
        localStorage.setItem('avatar_url', apiAvatar)
      }
    } catch (e) {
      // on ignore les erreurs réseau ici
    }
  }
})

function logout() {
  localStorage.clear()
  window.location.href = '/login'
}

function onAvatarError() {  try { localStorage.removeItem("avatar_url") } catch {}  avatarUrl.value = null }
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
</style>


