<template>
  <header class="d-flex align-items-center justify-content-between bg-white px-4 py-2 shadow-sm">
    <div>
      <span class="fw-bold fs-5">Bienvenue {{ pseudo }} sur COVA&nbsp;!</span>
    </div>
    <div class="d-flex align-items-center">
      <img v-if="avatarUrl" :src="avatarUrl" alt="Avatar" class="rounded-circle me-2" width="40" height="40" @error="onAvatarError" />
      <span class="me-3">{{ pseudo }}</span>
      <button class="btn btn-outline-danger btn-sm" @click="logout">Déconnexion</button>
    </div>
    <button @click="toggleDarkMode" class="btn btn-outline-secondary ms-2" title="Activer/désactiver le mode sombre">
      <i :class="isDark ? 'bi bi-moon-fill' : 'bi bi-brightness-high-fill'"></i>
    </button>
  </header>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const pseudo = ref('')
const avatarUrl = ref(null)

onMounted(async () => {
  // Lecture immédiate depuis le storage pour un rendu rapide
  pseudo.value = localStorage.getItem('pseudo') || 'Utilisateur'
  avatarUrl.value = localStorage.getItem('avatar_url') || null

  // Rafraîchir depuis l'API pour garantir la persistance
  const token = localStorage.getItem('access_token')
  if (token) {
    try {
      const res = await axios.get('http://localhost:5000/api/me', {
        headers: { Authorization: `Bearer ${token}` }
      })
      if (res.data?.pseudo) {
        pseudo.value = res.data.pseudo
        localStorage.setItem('pseudo', res.data.pseudo)
      }
      const apiAvatar = res.data?.avatar_url || (res.data?.avatar ? `http://localhost:5000/static/avatars/${res.data.avatar}` : null)
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

// Ces refs/fonctions peuvent être fournies ailleurs; laissées non définies si inutilisées
// const isDark = ref(false)
// function toggleDarkMode() { isDark.value = !isDark.value }
function onAvatarError() {  try { localStorage.removeItem("avatar_url") } catch {}  avatarUrl.value = null }
</script>


