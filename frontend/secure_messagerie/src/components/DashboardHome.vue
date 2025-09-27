<template>
  <div class="container py-4">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="card p-5 shadow-lg text-center animate__animated animate__fadeIn">
          <h2 class="mb-2 display-5 fw-bold">Bienvenue {{ pseudo }} ??</h2>
          <div v-if="avatarUrl" class="mb-3">
            <img :src="avatarUrl" alt="Avatar" class="avatar-lg" @error="onAvatarError" />
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
import { ref, onMounted } from 'vue'
import { api } from '@/utils/api'

const apiOk = ref(false)
const pseudo = ref('Utilisateur')
const avatarUrl = ref(null)

onMounted(async () => {
  pseudo.value = localStorage.getItem('pseudo') || 'Utilisateur'
  avatarUrl.value = localStorage.getItem('avatar_url') || null

  try {
    await api.get('/ping')
    apiOk.value = true
  } catch (e) {
    apiOk.value = false
  }

  const token = localStorage.getItem('access_token')
  if (token) {
    try {
      const res = await api.get('/me')
      if (res.data?.avatar_url) {
        avatarUrl.value = res.data.avatar_url
        localStorage.setItem('avatar_url', res.data.avatar_url)
      }
    } catch (e) {
      // ignore
    }
  }
})

function onAvatarError() {
  try { localStorage.removeItem('avatar_url') } catch {}
  avatarUrl.value = null
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
</style>
