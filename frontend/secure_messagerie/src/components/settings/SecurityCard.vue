<template>
  <div class="card p-3 h-100">
    <!-- Mot de passe -->
    <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
      <div>
        <h4 class="mb-1">Mot de passe</h4>
        <p class="text-muted small mb-0">
          Renforcez votre secret d'accès sans afficher vos informations sensibles dans l'interface.
        </p>
      </div>
      <button class="btn btn-outline-primary" @click="openPasswordModal" :disabled="savingPwd">
        <i class="bi bi-shield-lock me-1"></i> Modifier
      </button>
    </div>
    <div v-if="pwdMsg" :class="['alert mt-3', pwdOk ? 'alert-success' : 'alert-danger']">{{ pwdMsg }}</div>

    <hr class="my-4" />

    <!-- TOTP -->
    <h4 class="mb-3">Double authentification (TOTP)</h4>

    <!-- TOTP activé -->
    <div v-if="totpEnabled" class="totp-card">
      <div class="alert alert-success d-flex align-items-center gap-2">
        <i class="bi bi-shield-lock-fill fs-5"></i>
        <div>
          <strong>Double authentification activée</strong>
          <div v-if="formattedTotpLock" class="small text-warning">
            Accès verrouillé jusqu'au {{ formattedTotpLock }}
          </div>
        </div>
      </div>
      <p class="mb-3">
        Chaque connexion nécessite maintenant un code TOTP généré par votre application d'authentification.
      </p>
      <div class="d-flex flex-wrap gap-2">
        <button v-if="recoveryCodes.length" class="btn btn-outline-secondary" @click="openRecoveryModal">
          <i class="bi bi-key me-1"></i>Afficher les codes de récupération
        </button>
        <button class="btn btn-outline-danger" @click="openDeactivateTotpModal" :disabled="loadingTotp">
          <span v-if="loadingTotp" class="spinner-border spinner-border-sm me-1"></span>
          Désactiver la double authentification
        </button>
      </div>
      <p class="text-muted small mt-3">
        Besoin de nouveaux codes ? Désactivez puis réactivez TOTP pour en générer d'autres.
      </p>
    </div>

    <!-- TOTP non activé -->
    <div v-else class="totp-card">
      <p class="mb-3">
        Renforcez la sécurité du compte en ajoutant une authentification à deux facteurs basée sur un code TOTP.
        Installez une application compatible (Google Authenticator, Microsoft Authenticator, Authy, 1Password).
      </p>

      <ol class="totp-steps mb-3">
        <li :class="{ active: totpStep === 1 }">Démarrer l'activation et scanner le QR code.</li>
        <li :class="{ active: totpStep === 2 }">Entrer le code généré par l'application.</li>
        <li :class="{ active: totpStep === 3 }">Sauvegarder les codes de récupération affichés.</li>
      </ol>

      <div v-if="hasTotpEnrollment" class="totp-enrollment mb-3">
        <div class="row g-3 align-items-center">
          <div class="col-md-auto text-center">
            <img :src="totpEnrollment.qr" alt="QR Code TOTP" class="totp-qr mb-2" />
            <div class="small text-muted">Scannez ce code avec votre application.</div>
          </div>
          <div class="col">
            <label class="form-label fw-semibold">Clé secrète</label>
            <div class="input-group copyable-field mb-3">
              <input class="form-control" :value="totpEnrollment.secret" readonly />
              <button class="btn btn-outline-secondary" type="button" @click="copyToClipboard(totpEnrollment.secret)">
                <i class="bi bi-clipboard"></i>
              </button>
            </div>
            <div class="mb-2">
              <small class="text-muted">Configuration manuelle :</small>
              <pre class="totp-uri">{{ totpEnrollment.provisioningUri }}</pre>
            </div>
            <div class="input-group mt-2">
              <input
                v-model.trim="totpCode"
                type="text"
                class="form-control"
                maxlength="6"
                placeholder="Code à 6 chiffres"
              />
              <button class="btn btn-primary" :disabled="loadingTotp || totpCode.length !== 6" @click="confirmTotp">
                <span v-if="loadingTotp" class="spinner-border spinner-border-sm"></span>
                <span v-else>Confirmer</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <button
        v-if="!hasTotpEnrollment"
        class="btn btn-outline-primary"
        :disabled="loadingTotp"
        @click="startActivation"
      >
        <span v-if="loadingTotp" class="spinner-border spinner-border-sm me-1"></span>
        Démarrer l'activation
      </button>
    </div>

    <div v-if="totpError" class="alert alert-danger mt-3">{{ totpError }}</div>
    <div v-if="totpSuccess" class="alert alert-success mt-3">{{ totpSuccess }}</div>

    <!-- Modale mot de passe -->
    <CustomModal v-model="showPasswordModal">
      <template #title>
        <i class="bi bi-lock-fill me-2"></i>Mettre à jour le mot de passe
      </template>

      <div class="mb-3">
        <label class="form-label">Mot de passe actuel</label>
        <input
          v-model="oldPassword"
          type="password"
          class="form-control"
          placeholder="Mot de passe actuel"
          autocomplete="current-password"
        />
      </div>
      <div class="mb-3">
        <label class="form-label">Nouveau mot de passe</label>
        <input
          v-model="newPassword"
          type="password"
          class="form-control"
          placeholder="Nouveau mot de passe"
          autocomplete="new-password"
        />
      </div>
      <div class="mb-3">
        <label class="form-label">Confirmer le nouveau mot de passe</label>
        <input
          v-model="newPassword2"
          type="password"
          class="form-control"
          placeholder="Confirmer le nouveau mot de passe"
          autocomplete="new-password"
        />
      </div>
      <div v-if="pwdModalMsg" :class="['alert', pwdModalOk ? 'alert-success' : 'alert-danger']">
        {{ pwdModalMsg }}
      </div>

      <template #footer>
        <button class="btn btn-outline-secondary" @click="closePasswordModal" :disabled="savingPwd">Annuler</button>
        <button class="btn btn-primary" @click="changePassword" :disabled="savingPwd">
          <span v-if="savingPwd" class="spinner-border spinner-border-sm me-1"></span>
          <span v-else>Enregistrer</span>
        </button>
      </template>
    </CustomModal>

    <!-- Modale codes de récupération -->
    <CustomModal v-model="showRecoveryModal">
      <template #title>
        <i class="bi bi-key me-2"></i>Codes de récupération
      </template>

      <p class="small text-muted mb-3">
        Conservez ces codes dans un endroit sûr. Chaque code n'est utilisable qu'une seule fois.
      </p>
      <ul class="recovery-list mb-0">
        <li v-for="code in recoveryCodes" :key="code">{{ code }}</li>
      </ul>

      <template #footer>
        <button class="btn btn-outline-secondary" @click="downloadRecoveryCodes">
          <i class="bi bi-download me-2"></i>Télécharger
        </button>
        <button class="btn btn-primary" @click="closeRecoveryModal">J'ai sauvegardé mes codes</button>
      </template>
    </CustomModal>

    <CustomModal v-model="showDeactivateTotpModal">
      <template #title>
        <i class="bi bi-shield-exclamation me-2"></i>Désactiver la double authentification
      </template>

      <p class="mb-3">
        Avant de désactiver TOTP, assurez-vous d'avoir une méthode de secours. Vos prochaines connexions
        redeviendront protégées uniquement par le mot de passe.
      </p>
      <ul class="text-muted small ps-3 mb-3">
        <li>Les codes de récupération associés seront invalidés.</li>
        <li>Vous pourrez réactiver TOTP à tout moment depuis cette page.</li>
      </ul>
      <div v-if="deactivateTotpError" class="alert alert-danger">
        {{ deactivateTotpError }}
      </div>

      <template #footer>
        <button class="btn btn-outline-secondary" @click="closeDeactivateTotpModal" :disabled="loadingTotp">
          Annuler
        </button>
        <button class="btn btn-danger" @click="confirmDeactivateTotp" :disabled="loadingTotp">
          <span v-if="loadingTotp" class="spinner-border spinner-border-sm me-1"></span>
          <span v-else>Désactiver</span>
        </button>
      </template>
    </CustomModal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { api } from '@/utils/api'
import CustomModal from '@/components/ui/CustomModal.vue'

const totpEnabled = ref(false)
const totpLockedUntil = ref(null)
const totpEnrollment = reactive({
  secret: '',
  qr: '',
  provisioningUri: '',
})
const totpStep = ref(1)
const totpCode = ref('')
const totpError = ref('')
const totpSuccess = ref('')
const recoveryCodes = ref([])
const showRecoveryModal = ref(false)
const showDeactivateTotpModal = ref(false)
const deactivateTotpError = ref('')
const loadingTotp = ref(false)

const oldPassword = ref('')
const newPassword = ref('')
const newPassword2 = ref('')
const savingPwd = ref(false)
const pwdMsg = ref('')
const pwdOk = ref(false)
const showPasswordModal = ref(false)
const pwdModalMsg = ref('')
const pwdModalOk = ref(true)

const hasTotpEnrollment = computed(() => !!totpEnrollment.qr)
const formattedTotpLock = computed(() => {
  if (!totpLockedUntil.value) return null
  try {
    return new Date(totpLockedUntil.value).toLocaleString()
  } catch {
    return totpLockedUntil.value
  }
})

onMounted(async () => {
  await fetchSecurity()
})

async function fetchSecurity() {
  try {
    const res = await api.get('/me/security')
    totpEnabled.value = !!res.data.totp_enabled
    totpLockedUntil.value = res.data.totp_locked_until || null
    totpStep.value = totpEnabled.value ? 3 : 1
  } catch (e) {
    totpEnabled.value = false
  }
}

function openPasswordModal() {
  resetPasswordFields()
  showPasswordModal.value = true
}
function closePasswordModal() {
  if (savingPwd.value) return
  showPasswordModal.value = false
  resetPasswordFields()
}
function resetPasswordFields() {
  oldPassword.value = ''
  newPassword.value = ''
  newPassword2.value = ''
  pwdModalMsg.value = ''
  pwdModalOk.value = true
}

function openDeactivateTotpModal() {
  deactivateTotpError.value = ''
  showDeactivateTotpModal.value = true
}

function closeDeactivateTotpModal() {
  if (loadingTotp.value) return
  deactivateTotpError.value = ''
  showDeactivateTotpModal.value = false
}

async function changePassword() {
  pwdModalMsg.value = ''
  pwdMsg.value = ''
  const current = String(oldPassword.value || '')
  const nextPwd = String(newPassword.value || '')
  const confirmPwd = String(newPassword2.value || '')
  if (!current.length || !nextPwd.length || !confirmPwd.length) {
    pwdModalOk.value = false
    pwdModalMsg.value = 'Veuillez remplir tous les champs.'
    return
  }
  if (nextPwd !== confirmPwd) {
    pwdModalOk.value = false
    pwdModalMsg.value = 'La confirmation ne correspond pas.'
    return
  }
  savingPwd.value = true
  try {
    await api.put('/me/password', {
      old_password: current,
      new_password: nextPwd,
    })
    pwdOk.value = true
    pwdMsg.value = 'Mot de passe mis à jour'
    pwdModalOk.value = true
    pwdModalMsg.value = 'Mot de passe mis à jour'
    setTimeout(() => {
      showPasswordModal.value = false
      resetPasswordFields()
    }, 600)
  } catch (e) {
    pwdOk.value = false
    const detail = e.response?.data?.error || e.response?.data?.detail || 'Erreur mise à jour mot de passe'
    pwdMsg.value = ''
    pwdModalOk.value = false
    pwdModalMsg.value = detail
  } finally {
    savingPwd.value = false
  }
}

async function startActivation() {
  totpError.value = ''
  totpSuccess.value = ''
  loadingTotp.value = true
  recoveryCodes.value = []
  try {
    const res = await api.post('/auth/totp/activate')
    totpEnrollment.secret = res.data.secret
    totpEnrollment.qr = `data:image/png;base64,${res.data.qr_code}`
    totpEnrollment.provisioningUri = res.data.provisioning_uri
    totpStep.value = 2
  } catch (e) {
    const detail = e.response?.data?.detail || e.message
    totpError.value = detail || 'Erreur lors de la génération du QR code.'
  } finally {
    loadingTotp.value = false
  }
}

async function confirmTotp() {
  totpError.value = ''
  totpSuccess.value = ''
  if (!totpCode.value || totpCode.value.length !== 6) {
    totpError.value = 'Veuillez saisir le code à 6 chiffres généré par votre application.'
    return
  }
  loadingTotp.value = true
  try {
    const res = await api.post('/auth/totp/confirm', { code: totpCode.value })
    totpEnabled.value = true
    totpSuccess.value = res.data.message || 'Double authentification activée.'
    recoveryCodes.value = Array.isArray(res.data.recovery_codes) ? res.data.recovery_codes : []
    showRecoveryModal.value = recoveryCodes.value.length > 0
    totpStep.value = 3
    totpEnrollment.secret = ''
    totpEnrollment.qr = ''
    totpEnrollment.provisioningUri = ''
    totpCode.value = ''
    await fetchSecurity()
  } catch (e) {
    const detail = e.response?.data?.detail || e.response?.data?.error || e.message
    totpError.value = detail || 'Erreur lors de la confirmation du code.'
  } finally {
    loadingTotp.value = false
  }
}

async function confirmDeactivateTotp() {
  deactivateTotpError.value = ''
  totpError.value = ''
  totpSuccess.value = ''
  loadingTotp.value = true
  try {
    const res = await api.post('/auth/totp/deactivate')
    totpEnabled.value = false
    totpSuccess.value = res.data.message || 'Double authentification désactivée.'
    totpEnrollment.secret = ''
    totpEnrollment.qr = ''
    totpEnrollment.provisioningUri = ''
    totpCode.value = ''
    recoveryCodes.value = []
    totpStep.value = 1
    showDeactivateTotpModal.value = false
    await fetchSecurity()
  } catch (e) {
    const detail = e.response?.data?.detail || e.response?.data?.error || e.message
    const message = detail || 'Impossible de désactiver la double authentification pour le moment.'
    deactivateTotpError.value = message
    totpError.value = message
  } finally {
    loadingTotp.value = false
  }
}

function openRecoveryModal() {
  if (recoveryCodes.value.length > 0) {
    showRecoveryModal.value = true
  }
}
function closeRecoveryModal() {
  showRecoveryModal.value = false
}

function downloadRecoveryCodes() {
  if (!recoveryCodes.value.length) return
  const content = [
    'Codes de récupération COVA',
    '-------------------------',
    ...recoveryCodes.value,
    '',
    'Conservez ces codes en lieu sûr.',
  ].join('\n')
  const blob = new Blob([content], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'codes-recuperation-cova.txt'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

async function copyToClipboard(value) {
  if (!value) return
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(value)
    } else {
      const textarea = document.createElement('textarea')
      textarea.value = value
      textarea.setAttribute('readonly', '')
      textarea.style.position = 'absolute'
      textarea.style.left = '-9999px'
      document.body.appendChild(textarea)
      textarea.select()
      document.execCommand('copy')
      document.body.removeChild(textarea)
    }
    totpSuccess.value = 'Copié dans le presse-papiers.'
    setTimeout(() => {
      totpSuccess.value = ''
    }, 1500)
  } catch {
    totpError.value = 'Impossible de copier automatiquement.'
  }
}
</script>

<style scoped src="@/assets/styles/settings.css"></style>

