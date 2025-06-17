<!-- src/components/Settings.vue -->
<template>
  <div class="p-4">
    <h2 class="mb-4"><i class="bi bi-gear"></i> Paramètres</h2>
    <div class="mb-5">
      <h4 class="mb-3">Avatar</h4>
      <div v-if="avatarUrl" class="mb-2">
        <img :src="avatarUrl" alt="Avatar" class="avatar-lg mb-2" />
        <div>
          <button class="btn btn-sm btn-danger" @click="deleteAvatar" :disabled="loadingAvatar">
            Supprimer l'avatar
          </button>
        </div>
      </div>
      <input type="file" class="form-control mt-2" @change="uploadAvatar" />
    </div>

    <hr />

    <div>
      <h4 class="mb-3">Double authentification (TOTP)</h4>
      <div v-if="totpEnabled">
        <p>La double authentification est activée.</p>
        <button class="btn btn-warning" @click="deactivateTotp" :disabled="loadingTotp">
          Désactiver
        </button>
      </div>
      <div v-else>
        <p>Active la double authentification pour sécuriser ton compte.</p>
        <button class="btn btn-primary mb-3" @click="startActivation" :disabled="loadingTotp">
          Activer
        </button>
        <div v-if="qrCodeData" class="mb-3">
          <img :src="qrCodeData" alt="QR Code" class="mb-2" />
          <input v-model="totpCode" type="text" class="form-control mb-2" placeholder="Code TOTP" />
          <button class="btn btn-success" @click="confirmTotp" :disabled="loadingTotp">
            Confirmer
          </button>
        </div>
      </div>
      <div v-if="totpError" class="alert alert-danger mt-2">{{ totpError }}</div>
      <div v-if="totpSuccess" class="alert alert-success mt-2">{{ totpSuccess }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const avatarUrl = ref(null)
const totpEnabled = ref(false)
const qrCodeData = ref(null)
const totpCode = ref('')
const totpError = ref('')
const totpSuccess = ref('')
const loadingAvatar = ref(false)
const loadingTotp = ref(false)

const token = localStorage.getItem('access_token')

onMounted(async () => {
  await fetchProfile()
  await fetchSecurity()
})

async function fetchProfile() {
  try {
    const res = await axios.get('http://localhost:5000/api/me', {
      headers: { Authorization: `Bearer ${token}` }
    })
    if (res.data.avatar) {
      avatarUrl.value = `http://localhost:5000/static/avatars/${res.data.avatar}`
    }
  } catch (e) {
    // ignore
  }
}

async function fetchSecurity() {
  try {
    const res = await axios.get('http://localhost:5000/api/me/security', {
      headers: { Authorization: `Bearer ${token}` }
    })
    totpEnabled.value = res.data.totp_enabled
  } catch (e) {
    // ignore
  }
}

async function uploadAvatar(event) {
  const file = event.target.files[0]
  if (!file) return
  loadingAvatar.value = true
  const formData = new FormData()
  formData.append('avatar', file)
  try {
    const res = await axios.post('http://localhost:5000/api/me/avatar', formData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    })
    avatarUrl.value = res.data.avatar_url
    localStorage.setItem('avatar_url', res.data.avatar_url)
  } catch (e) {
    totpError.value = e.response?.data?.error || 'Erreur lors de l\'upload'
  } finally {
    loadingAvatar.value = false
  }
}

async function deleteAvatar() {
  loadingAvatar.value = true
  try {
    await axios.delete('http://localhost:5000/api/me/avatar', {
      headers: { Authorization: `Bearer ${token}` }
    })
    avatarUrl.value = null
    localStorage.removeItem('avatar_url')
  } catch (e) {
    // ignore
  } finally {
    loadingAvatar.value = false
  }
}

async function startActivation() {
  totpError.value = ''
  totpSuccess.value = ''
  loadingTotp.value = true
  try {
    const res = await axios.post('http://localhost:5000/api/auth/totp/activate', null, {
      responseType: 'blob',
      headers: { Authorization: `Bearer ${token}` }
    })
    const reader = new FileReader()
    reader.onloadend = () => {
      qrCodeData.value = reader.result
    }
    reader.readAsDataURL(res.data)
  } catch (e) {
    totpError.value = 'Erreur lors de la génération du QR code'
  } finally {
    loadingTotp.value = false
  }
}

async function confirmTotp() {
  totpError.value = ''
  totpSuccess.value = ''
  loadingTotp.value = true
  try {
    const res = await axios.post('http://localhost:5000/api/auth/totp/confirm', { code: totpCode.value }, {
      headers: { Authorization: `Bearer ${token}` }
    })
    totpEnabled.value = true
    qrCodeData.value = null
    totpCode.value = ''
    totpSuccess.value = res.data.message || 'TOTP activé'
  } catch (e) {
    totpError.value = e.response?.data?.error || 'Erreur de confirmation'
  } finally {
    loadingTotp.value = false
  }
}

async function deactivateTotp() {
  totpError.value = ''
  totpSuccess.value = ''
  loadingTotp.value = true
  try {
    const res = await axios.post('http://localhost:5000/api/auth/totp/deactivate', null, {
      headers: { Authorization: `Bearer ${token}` }
    })
    totpEnabled.value = false
    totpSuccess.value = res.data.message || 'TOTP désactivé'
  } catch (e) {
    totpError.value = e.response?.data?.error || 'Erreur de désactivation'
  } finally {
    loadingTotp.value = false
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
</style>
