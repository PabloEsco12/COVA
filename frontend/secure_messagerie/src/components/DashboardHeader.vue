<template>
  <header class="d-flex align-items-center justify-content-between bg-white px-4 py-2 shadow-sm">
    <div>
      <span class="fw-bold fs-5">Bienvenue sur COVA&nbsp;!</span>
    </div>
    <div class="d-flex align-items-center">
      <img :src="avatarUrl" alt="Avatar" class="rounded-circle me-2" width="40" height="40" v-if="avatarUrl" />
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

const pseudo = ref('')
const avatarUrl = ref(null)

onMounted(() => {
  // À compléter avec une requête API pour charger le profil utilisateur
  pseudo.value = localStorage.getItem('pseudo') || 'Utilisateur'
  avatarUrl.value = localStorage.getItem('avatar_url') || null
})

function logout() {
  localStorage.clear()
  window.location.href = "/login"
}
</script>
