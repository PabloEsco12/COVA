<!-- src/components/Settings.vue (revamped) -->
<template>
  <div class="p-4">
    <h2 class="mb-4"><i class="bi bi-gear"></i> Paramètres</h2>

    <div class="row g-4">
      <div class="col-lg-6">
        <div class="card p-3 h-100">
          <h4 class="mb-3">Profil</h4>
          <div class="mb-3">
            <label class="form-label">Pseudo</label>
            <div class="input-group">
              <input v-model.trim="formPseudo" class="form-control" />
              <button class="btn btn-outline-primary" @click="savePseudo" :disabled="savingPseudo">
                <span v-if="savingPseudo" class="spinner-border spinner-border-sm"></span>
                <span v-else>Enregistrer</span>
              </button>
            </div>
          </div>
          <div>
            <label class="form-label">Email</label>
            <div class="input-group">
              <input v-model.trim="formEmail" class="form-control" type="email" />
              <button class="btn btn-outline-primary" @click="saveEmail" :disabled="savingEmail">
                <span v-if="savingEmail" class="spinner-border spinner-border-sm"></span>
                <span v-else>Enregistrer</span>
              </button>
            </div>
          </div>
          <div v-if="profileMsg" :class="['alert mt-3', profileOk ? 'alert-success' : 'alert-danger']">{{ profileMsg }}</div>
        </div>
      </div>
      <div class="col-lg-6">
        <div class="card p-3 h-100">
          <h4 class="mb-3">Mot de passe</h4>
          <div class="mb-2"><input v-model="oldPassword" type="password" class="form-control" placeholder="Mot de passe actuel" autocomplete="current-password" /></div>
          <div class="mb-2"><input v-model="newPassword" type="password" class="form-control" placeholder="Nouveau mot de passe" autocomplete="new-password" /></div>
          <div class="mb-2"><input v-model="newPassword2" type="password" class="form-control" placeholder="Confirmer le nouveau mot de passe" autocomplete="new-password" /></div>
          <div class="d-flex justify-content-end">
            <button class="btn btn-outline-primary" @click="changePassword" :disabled="savingPwd">
              <span v-if="savingPwd" class="spinner-border spinner-border-sm"></span>
              <span v-else>Mettre à jour</span>
            </button>
          </div>
          <div v-if="pwdMsg" :class="['alert mt-3', pwdOk ? 'alert-success' : 'alert-danger']">{{ pwdMsg }}</div>
        </div>
      </div>
    </div>

    <hr />

    <div class="mt-4">
      <h4 class="mb-3">Double authentification (TOTP)</h4>
      <div v-if="totpEnabled">
        <p>La double authentification est activée.</p>
        <button class="btn btn-warning" @click="deactivateTotp" :disabled="loadingTotp">Désactiver</button>
      </div>
      <div v-else>
        <p>Active la double authentification pour sécuriser ton compte.</p>
        <button class="btn btn-primary mb-3" @click="startActivation" :disabled="loadingTotp">Activer</button>
        <div v-if="qrCodeData" class="mb-3">
          <img :src="qrCodeData" alt="QR Code" class="mb-2" />
          <input v-model="totpCode" type="text" class="form-control mb-2" placeholder="Code TOTP" />
          <button class="btn btn-success" @click="confirmTotp" :disabled="loadingTotp">Confirmer</button>
        </div>
      </div>
      <div v-if="totpError" class="alert alert-danger mt-2">{{ totpError }}</div>
      <div v-if="totpSuccess" class="alert alert-success mt-2">{{ totpSuccess }}</div>
    </div>

    <hr />

    <div class="row g-4">
      <div class="col-lg-6">
        <div class="card p-3 h-100">
          <h4 class="mb-3">Notifications</h4>
          <div class="form-check form-switch mb-2">
            <input class="form-check-input" type="checkbox" id="notifLogin" v-model="notifLogin" @change="saveSecurity" />
            <label for="notifLogin" class="form-check-label">Recevoir un e‑mail lors d'une connexion</label>
          </div>
          <div class="form-check form-switch mb-2">
            <input class="form-check-input" type="checkbox" id="notifBrowser" v-model="notifBrowser" @change="toggleBrowserNotifications" />
            <label for="notifBrowser" class="form-check-label">Notifications navigateur (nouveaux messages)</label>
          </div>
          <button class="btn btn-outline-secondary btn-sm" @click="testNotification" :disabled="!notifBrowser">Tester la notification</button>
          <div v-if="secMsg" class="alert alert-info mt-3">{{ secMsg }}</div>
        </div>
      </div>
      <div class="col-lg-6">
        <div class="card p-3 h-100">
          <h4 class="mb-3">Avatar</h4>
          <div v-if="avatarUrl" class="mb-2">
            <img :src="avatarUrl" alt="Avatar" class="avatar-lg mb-2" />
            <div>
              <button class="btn btn-sm btn-danger" @click="deleteAvatar" :disabled="loadingAvatar">Supprimer l'avatar</button>
            </div>
          </div>
          <input type="file" class="form-control mt-2" @change="uploadAvatar" />
        </div>
      </div>
    </div>

    <hr class="my-5" />

    <div class="danger-zone p-3 border rounded-3">
      <h4 class="text-danger mb-2"><i class="bi bi-exclamation-triangle-fill me-1"></i> Zone dangereuse</h4>
      <p class="mb-3">
        Supprimer votre compte effacera définitivement vos données associées (conversations, messages liés, appareils, etc.). Cette action est irréversible.
      </p>
      <button class="btn btn-outline-danger" @click="openDeleteModal" :disabled="loadingDelete">
        <span v-if="loadingDelete" class="spinner-border spinner-border-sm me-2"></span>
        Supprimer mon compte
      </button>
      <div v-if="deleteError" class="alert alert-danger mt-3">{{ deleteError }}</div>
    </div>

    <!-- Modal de confirmation de suppression -->
    <div v-if="showDeleteModal" class="modal-backdrop fade show"></div>
    <div v-if="showDeleteModal" class="custom-modal d-block" tabindex="-1" role="dialog" aria-modal="true">
      <div class="custom-modal-dialog">
        <div class="custom-modal-content">
          <div class="custom-modal-header">
            <h5 class="custom-modal-title text-danger"><i class="bi bi-trash3-fill me-2"></i>Confirmer la suppression</h5>
            <button type="button" class="btn-close" aria-label="Close" @click="closeDeleteModal"></button>
          </div>
          <div class="custom-modal-body">
            <p class="mb-3">Cette action est irréversible. Veuillez saisir votre mot de passe pour confirmer la suppression définitive de votre compte.</p>
            <input v-model="deletePassword" type="password" class="form-control" placeholder="Mot de passe" autocomplete="current-password" />
            <div v-if="deleteError" class="alert alert-danger mt-3">{{ deleteError }}</div>
          </div>
          <div class="custom-modal-footer">
            <button class="btn btn-secondary" @click="closeDeleteModal" :disabled="loadingDelete">Annuler</button>
            <button class="btn btn-danger" @click="confirmDelete" :disabled="!deletePassword || loadingDelete">
              <span v-if="loadingDelete" class="spinner-border spinner-border-sm me-2"></span>
              Supprimer définitivement
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { api, backendBase } from '@/utils/api'

const avatarUrl = ref(null)
const formPseudo = ref('')
const formEmail = ref('')
const profileMsg = ref('')
const profileOk = ref(false)
const savingPseudo = ref(false)
const savingEmail = ref(false)

const totpEnabled = ref(false)
const qrCodeData = ref(null)
const totpCode = ref('')
const totpError = ref('')
const totpSuccess = ref('')
const loadingAvatar = ref(false)
const loadingTotp = ref(false)
const loadingDelete = ref(false)
const deleteError = ref('')
const showDeleteModal = ref(false)
const deletePassword = ref('')

const notifLogin = ref(false)
const notifBrowser = ref(localStorage.getItem('notif_browser') === '1')
const secMsg = ref('')

const oldPassword = ref('')
const newPassword = ref('')
const newPassword2 = ref('')
const savingPwd = ref(false)
const pwdMsg = ref('')
const pwdOk = ref(false)

const token = localStorage.getItem('access_token')
const router = useRouter()

onMounted(async () => {
  await fetchProfile()
  await fetchSecurity()
})

async function fetchProfile() {
  try {
    const res = await api.get(`/me`)
    formPseudo.value = res.data.pseudo || ''
    formEmail.value = res.data.email || ''
    
    avatarUrl.value = res.data.avatar_url || (res.data.avatar ? `${backendBase}/static/avatars/${res.data.avatar}` : null)
  } catch (e) {
    // ignore
  }
}

async function fetchSecurity() {
  try {
    const res = await api.get(`/me/security`)
    totpEnabled.value = res.data.totp_enabled
    notifLogin.value = !!res.data.notification_login
  } catch (e) {
    // ignore
  }
}

async function savePseudo() {
  profileMsg.value = ''
  savingPseudo.value = true
  try {
    await api.put(`/me/pseudo`, { pseudo: formPseudo.value })
    profileOk.value = true
    profileMsg.value = 'Pseudo mis à jour'
    localStorage.setItem('pseudo', formPseudo.value)
  } catch (e) {
    profileOk.value = false
    profileMsg.value = e.response?.data?.error || 'Erreur mise à jour pseudo'
  } finally { savingPseudo.value = false }
}

async function saveEmail() {
  profileMsg.value = ''
  savingEmail.value = true
  try {
    await api.put(`/me/email`, { email: formEmail.value })
    profileOk.value = true
    profileMsg.value = 'Email mis à jour'
  } catch (e) {
    profileOk.value = false
    profileMsg.value = e.response?.data?.error || 'Erreur mise à jour email'
  } finally { savingEmail.value = false }
}

async function changePassword() {
  pwdMsg.value = ''
  if (!oldPassword.value || !newPassword.value || newPassword.value !== newPassword2.value) {
    pwdOk.value = false
    pwdMsg.value = 'Vérifiez les champs renseignés'
    return
  }
  savingPwd.value = true
  try {
    await api.put(`/me/password`, { old_password: oldPassword.value, new_password: newPassword.value })
    pwdOk.value = true
    pwdMsg.value = 'Mot de passe mis à jour'
    oldPassword.value = newPassword.value = newPassword2.value = ''
  } catch (e) {
    pwdOk.value = false
    pwdMsg.value = e.response?.data?.error || 'Erreur mise à jour mot de passe'
  } finally { savingPwd.value = false }
}

async function saveSecurity() {
  try {
    await api.put(`/me/security`, { notification_login: notifLogin.value })
    secMsg.value = 'Paramètres de sécurité enregistrés'
    setTimeout(() => secMsg.value = '', 1500)
  } catch {}
}

function toggleBrowserNotifications() {
  if (notifBrowser.value) {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then(p => {
        if (p !== 'granted') notifBrowser.value = false
        localStorage.setItem('notif_browser', notifBrowser.value ? '1' : '0')
      })
    } else {
      localStorage.setItem('notif_browser', '1')
    }
  } else {
    localStorage.setItem('notif_browser', '0')
  }
}

function testNotification() {
  if (!notifBrowser.value || !('Notification' in window) || Notification.permission !== 'granted') return
  const n = new Notification('Test de notification', { body: 'Ceci est un test COVA.' })
  setTimeout(() => n.close(), 3000)
}

async function uploadAvatar(event) {
  const file = event.target.files?.[0]
  if (!file) return
  loadingAvatar.value = true
  const formData = new FormData()
  formData.append('avatar', file)
  try {
    const res = await api.post(`/me/avatar`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    avatarUrl.value = res.data.avatar_url
    localStorage.setItem('avatar_url', res.data.avatar_url)
  } catch (e) {
    totpError.value = e.response?.data?.error || "Erreur lors de l'upload"
  } finally {
    loadingAvatar.value = false
  }
}

async function deleteAvatar() {
  loadingAvatar.value = true
  try {
    await api.delete(`/me/avatar`)
    avatarUrl.value = null
    localStorage.removeItem('avatar_url')
  } catch (e) {
  } finally {
    loadingAvatar.value = false
  }
}

async function startActivation() {
  totpError.value = ''
  totpSuccess.value = ''
  loadingTotp.value = true
  try {
    const res = await api.post(`/auth/totp/activate`, null, { responseType: 'blob' })
    const reader = new FileReader()
    reader.onloadend = () => { qrCodeData.value = reader.result }
    reader.readAsDataURL(res.data)
  } catch (e) {
    totpError.value = 'Erreur lors de la génération du QR code'
  } finally { loadingTotp.value = false }
}

async function confirmTotp() {
  totpError.value = ''
  totpSuccess.value = ''
  loadingTotp.value = true
  try {
    const res = await api.post(`/auth/totp/confirm`, { code: totpCode.value })
    totpEnabled.value = true
    qrCodeData.value = null
    totpCode.value = ''
    totpSuccess.value = res.data.message || 'TOTP activé'
  } catch (e) {
    totpError.value = e.response?.data?.error || 'Erreur de confirmation'
  } finally { loadingTotp.value = false }
}

async function deactivateTotp() {
  totpError.value = ''
  totpSuccess.value = ''
  loadingTotp.value = true
  try {
    const res = await api.post(`/auth/totp/deactivate`, null)
    totpEnabled.value = false
    totpSuccess.value = res.data.message || 'TOTP désactivé'
  } catch (e) {
    totpError.value = e.response?.data?.error || 'Erreur de désactivation'
  } finally { loadingTotp.value = false }
}

function openDeleteModal() { deleteError.value = ''; deletePassword.value = ''; showDeleteModal.value = true }
function closeDeleteModal() { if (!loadingDelete.value) showDeleteModal.value = false }
async function confirmDelete() {
  deleteError.value = ''
  loadingDelete.value = true
  try {
    await api.delete(`/me`, { data: { password: deletePassword.value } })
    localStorage.clear(); router.push('/login')
  } catch (e) {
    deleteError.value = e.response?.data?.error || 'Suppression impossible pour le moment.'
  } finally { loadingDelete.value = false }
}
</script>

<style scoped>
.avatar-lg { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; box-shadow: 0 2px 8px #0002; }
.danger-zone { background: #fffaf9 }

/* Modal custom léger basé sur Bootstrap */
.custom-modal { position: fixed; top: 0; left: 0; right:0; bottom:0; display:flex; align-items:center; justify-content:center; z-index: 1050; }
.custom-modal-dialog { max-width: 520px; width: 92%; }
.custom-modal-content { background: #fff; border-radius: .75rem; box-shadow: 0 12px 40px rgba(0,0,0,.15); overflow: hidden; }
.custom-modal-header { display:flex; align-items:center; justify-content:space-between; padding: .85rem 1rem; border-bottom: 1px solid #eee; }
.custom-modal-title { margin: 0; }
.custom-modal-body { padding: 1rem; }
.custom-modal-footer { display:flex; gap:.5rem; justify-content:flex-end; padding: .85rem 1rem; border-top: 1px solid #eee; }
.modal-backdrop.show { opacity: .25; }
</style>
