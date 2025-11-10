<!-- src/components/Settings.vue (revamped) -->
<template>
  <div class="p-4">
    <h2 class="mb-4"><i class="bi bi-gear"></i> Parametres</h2>

    <div class="row g-4">
      <div class="col-lg-6">
        <div class="card p-3 h-100">
          <h4 class="mb-3">Profil</h4>
          <div class="mb-3">
            <label class="form-label">Adresse e-mail</label>
            <input class="form-control" :value="emailDisplay" disabled />
          </div>
          <div class="mb-3">
            <label class="form-label">Nom d'affichage</label>
            <input v-model.trim="formPseudo" class="form-control" placeholder="Nom visible par vos interlocuteurs" />
          </div>
          <div class="row g-2">
            <div class="col-md-6">
              <label class="form-label">Fonction</label>
              <input v-model.trim="formJobTitle" class="form-control" placeholder="Ex. Responsable Securite" />
            </div>
            <div class="col-md-6">
              <label class="form-label">Departement / Equipe</label>
              <input v-model.trim="formDepartment" class="form-control" placeholder="Ex. SOC Europe" />
            </div>
          </div>
          <div class="row g-2 mt-2">
            <div class="col-md-6">
              <label class="form-label">Numero de telephone securise</label>
              <input v-model.trim="formPhone" class="form-control" placeholder="+32 ..." />
            </div>
            <div class="col-md-6">
              <label class="form-label">Fuseau horaire</label>
              <select v-model="formTimezone" class="form-select">
                <option v-for="tz in timezoneOptions" :key="tz" :value="tz">{{ tz }}</option>
              </select>
            </div>
          </div>
          <div class="row g-2 mt-2">
            <div class="col-md-6">
              <label class="form-label">Langue preferee</label>
              <select v-model="formLocale" class="form-select">
                <option v-for="loc in localeOptions" :key="loc.value" :value="loc.value">{{ loc.label }}</option>
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label">Message d'etat</label>
              <input v-model.trim="formStatus" class="form-control" placeholder="Disponible, en deplacement…" />
            </div>
          </div>
          <div class="mt-3">
            <label class="form-label">Cle publique PGP (optionnel)</label>
            <textarea v-model.trim="formPgp" class="form-control" rows="3" placeholder="-----BEGIN PGP PUBLIC KEY BLOCK-----"></textarea>
          </div>
          <div class="d-flex justify-content-end mt-3">
            <button class="btn btn-outline-primary" @click="saveProfile" :disabled="savingProfile">
              <span v-if="savingProfile" class="spinner-border spinner-border-sm"></span>
              <span v-else>Enregistrer le profil</span>
            </button>
          </div>
          <div v-if="profileMsg" :class="['alert mt-3', profileOk ? 'alert-success' : 'alert-danger']">{{ profileMsg }}</div>
        </div>
      </div>
      <div class="col-lg-6">
        <div class="card p-3 h-100">
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

          <h4 class="mb-3">Double authentification (TOTP)</h4>

          <div v-if="totpEnabled" class="totp-card">
            <div class="alert alert-success d-flex align-items-center gap-2">
              <i class="bi bi-shield-lock-fill fs-5"></i>
              <div>
                <strong>Double authentification activee</strong>
                <div v-if="formattedTotpLock" class="small text-warning">Acces verrouille jusqu'au {{ formattedTotpLock }}</div>
              </div>
            </div>
            <p class="mb-3">Chaque connexion necessite maintenant un code TOTP genere par votre application d'authentification.</p>
            <div class="d-flex flex-wrap gap-2">
              <button v-if="recoveryCodes.length" class="btn btn-outline-secondary" @click="openRecoveryModal">
                <i class="bi bi-key me-1"></i>Afficher les codes de recuperation
              </button>
              <button class="btn btn-outline-danger" @click="deactivateTotp" :disabled="loadingTotp">
                <span v-if="loadingTotp" class="spinner-border spinner-border-sm me-1"></span>
                Desactiver la double authentification
              </button>
            </div>
            <p class="text-muted small mt-3">
              Besoin de nouveaux codes ? Desactivez puis reactivez TOTP pour en generer d'autres.
            </p>
          </div>

          <div v-else class="totp-card">
            <p class="mb-3">
              Renforcez la securite du compte en ajoutant une authentification a deux facteurs basee sur un code TOTP.
              Installez une application compatible (Google Authenticator, Microsoft Authenticator, Authy, 1Password).
            </p>

            <ol class="totp-steps mb-3">
              <li :class="{ active: totpStep === 1 }">Demarrer l'activation et scanner le QR code.</li>
              <li :class="{ active: totpStep === 2 }">Entrer le code genere par l'application.</li>
              <li :class="{ active: totpStep === 3 }">Sauvegarder les codes de recuperation affiches.</li>
            </ol>

            <div v-if="hasTotpEnrollment" class="totp-enrollment mb-3">
              <div class="row g-3 align-items-center">
                <div class="col-md-auto text-center">
                  <img :src="totpEnrollment.qr" alt="QR Code TOTP" class="totp-qr mb-2" />
                  <div class="small text-muted">Scannez ce code avec votre application.</div>
                </div>
                <div class="col">
                  <label class="form-label fw-semibold">Cle secrete</label>
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
                    <input v-model.trim="totpCode" type="text" class="form-control" maxlength="6" placeholder="Code a 6 chiffres" />
                    <button class="btn btn-primary" :disabled="loadingTotp || totpCode.length !== 6" @click="confirmTotp">
                      <span v-if="loadingTotp" class="spinner-border spinner-border-sm"></span>
                      <span v-else>Confirmer</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <button v-if="!hasTotpEnrollment" class="btn btn-outline-primary" :disabled="loadingTotp" @click="startActivation">
              <span v-if="loadingTotp" class="spinner-border spinner-border-sm me-1"></span>
              Demarrer l'activation
            </button>
          </div>

          <div v-if="totpError" class="alert alert-danger mt-3">{{ totpError }}</div>
          <div v-if="totpSuccess" class="alert alert-success mt-3">{{ totpSuccess }}</div>
        </div>
      </div>
    </div>

    <div v-if="showPasswordModal" class="modal-backdrop fade show"></div>
    <div v-if="showPasswordModal" class="custom-modal d-block" tabindex="-1" role="dialog" aria-modal="true">
      <div class="custom-modal-dialog">
        <div class="custom-modal-content">
          <div class="custom-modal-header">
            <h5 class="custom-modal-title"><i class="bi bi-lock-fill me-2"></i>Mettre à jour le mot de passe</h5>
            <button class="btn btn-sm btn-outline-secondary" @click="closePasswordModal" :disabled="savingPwd">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
          <div class="custom-modal-body">
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
          </div>
          <div class="custom-modal-footer">
            <button class="btn btn-outline-secondary" @click="closePasswordModal" :disabled="savingPwd">Annuler</button>
            <button class="btn btn-primary" @click="changePassword" :disabled="savingPwd">
              <span v-if="savingPwd" class="spinner-border spinner-border-sm me-1"></span>
              <span v-else>Enregistrer</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showRecoveryModal" class="modal-backdrop fade show"></div>
    <div v-if="showRecoveryModal" class="custom-modal d-block" tabindex="-1" role="dialog" aria-modal="true">
      <div class="custom-modal-dialog">
        <div class="custom-modal-content">
          <div class="custom-modal-header">
            <h5 class="custom-modal-title"><i class="bi bi-key me-2"></i>Codes de recuperation</h5>
            <button type="button" class="btn-close" aria-label="Fermer" @click="closeRecoveryModal"></button>
          </div>
          <div class="custom-modal-body">
            <p class="small text-muted mb-3">Conservez ces codes dans un endroit sur. Chaque code n'est utilisable qu'une seule fois.</p>
            <ul class="recovery-list mb-0">
              <li v-for="code in recoveryCodes" :key="code">{{ code }}</li>
            </ul>
          </div>
          <div class="custom-modal-footer">
            <button class="btn btn-outline-secondary" @click="downloadRecoveryCodes"><i class="bi bi-download me-2"></i>Telecharger</button>
            <button class="btn btn-primary" @click="closeRecoveryModal">J'ai sauvegarde mes codes</button>
          </div>
        </div>
      </div>
    </div>

    <hr />

    <div class="row g-4">
      <div class="col-lg-6">
        <div class="card p-3 h-100">
          <div class="d-flex justify-content-between align-items-start mb-3">
            <div>
              <h4 class="mb-1">Notifications</h4>
              <p class="text-muted small mb-0">Configurez la facon dont SecureChat vous alerte des activites sensibles.</p>
            </div>
            <i class="bi bi-bell text-secondary fs-4"></i>
          </div>

          <div class="border rounded-3 p-3 mb-3">
            <div class="d-flex justify-content-between align-items-start">
              <div class="me-3">
                <h5 class="h6 mb-1">Alertes de connexion par e-mail</h5>
                <p class="text-muted small mb-2">Recevez un resume securise a chaque authentification reussie.</p>
              </div>
              <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="notifLogin" v-model="notifLogin" @change="saveSecurity" :disabled="!preferencesLoaded" />
              </div>
            </div>
            <div class="row g-2 mt-2">
              <div class="col-md-6">
                <label for="quietStart" class="form-label small text-muted mb-1">Plage silencieuse (de)</label>
                <input id="quietStart" type="time" class="form-control form-control-sm" v-model="emailQuietStart" :disabled="loadingEmailPref || !preferencesLoaded" />
              </div>
              <div class="col-md-6">
                <label for="quietEnd" class="form-label small text-muted mb-1">Plage silencieuse (a)</label>
                <input id="quietEnd" type="time" class="form-control form-control-sm" v-model="emailQuietEnd" :disabled="loadingEmailPref || !preferencesLoaded" />
              </div>
            </div>
            <div class="d-flex flex-wrap gap-2 mt-3">
              <button class="btn btn-outline-primary btn-sm" @click="saveEmailPreference" :disabled="loadingEmailPref || !preferencesLoaded">
                <span v-if="loadingEmailPref" class="spinner-border spinner-border-sm me-1"></span>
                Enregistrer les preferences e-mail
              </button>
              <button class="btn btn-outline-secondary btn-sm" @click="sendLoginAlertTest" :disabled="sendingTestEmail || !notifLogin || !preferencesLoaded">
                <span v-if="sendingTestEmail" class="spinner-border spinner-border-sm me-1"></span>
                Envoyer un e-mail de test
              </button>
            </div>
            <p class="text-muted small mt-2 mb-0">Les alertes critiques restent envoyees immediatement, meme pendant la plage silencieuse.</p>
            <div v-if="emailPrefMsg" :class="['alert mt-3', emailPrefOk ? 'alert-success' : 'alert-danger']">{{ emailPrefMsg }}</div>
          </div>

          <div class="border rounded-3 p-3">
            <div class="d-flex justify-content-between align-items-start">
              <div class="me-3">
                <h5 class="h6 mb-1">Notifications navigateur en temps reel</h5>
                <p class="text-muted small mb-2">Soyez prevenu instantanement lorsqu'un message confidentiel arrive.</p>
              </div>
              <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="notifBrowser" :disabled="!browserSupported || syncingPushPref" v-model="notifBrowser" @change="toggleBrowserNotifications" />
              </div>
            </div>
            <div class="d-flex flex-wrap gap-2">
              <button class="btn btn-outline-secondary btn-sm" @click="testNotification" :disabled="!notifBrowser || browserPermission !== 'granted'">Tester une notification</button>
            </div>
            <div class="mt-2">
              <p v-if="!browserSupported" class="text-muted small mb-0">Votre navigateur ne prend pas en charge les notifications push.</p>
              <p v-else-if="browserPermission === 'denied'" class="text-danger small mb-0">Autorisez SecureChat depuis les parametres de votre navigateur pour recevoir les alertes.</p>
              <p v-else-if="browserPermission === 'default'" class="text-muted small mb-0">Nous vous demanderons l'autorisation lors de l'activation.</p>
              <p v-else class="text-muted small mb-0">Notifications actives sur ce navigateur.</p>
            </div>
            <div v-if="browserMsg" :class="['alert mt-3', browserMsgType === 'success' ? 'alert-success' : browserMsgType === 'error' ? 'alert-danger' : browserMsgType === 'warning' ? 'alert-warning' : 'alert-info']">{{ browserMsg }}</div>
          </div>

          <div
            v-if="secMsg"
            :class="[
              'alert mt-3',
              secMsgType === 'error'
                ? 'alert-danger'
                : secMsgType === 'success'
                  ? 'alert-success'
                  : 'alert-info',
            ]"
          >
            {{ secMsg }}
          </div>
        </div>
      </div>
      <div class="col-lg-6">
        <div class="card p-3 h-100">
          <h4 class="mb-3">Avatar</h4>
          <div class="avatar-settings d-flex align-items-center gap-3 mb-3">
            <div class="avatar-preview-wrapper">
              <img v-if="avatarUrl" :src="avatarUrl" alt="Avatar" class="avatar-preview" />
              <div v-else class="avatar-placeholder">{{ avatarInitials }}</div>
            </div>
            <div class="flex-grow-1">
              <div class="d-flex flex-wrap gap-2">
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  class="form-control form-control-sm avatar-input"
                  @change="uploadAvatar"
                  :disabled="loadingAvatar"
                />
                <button class="btn btn-sm btn-outline-danger" @click="deleteAvatar" :disabled="loadingAvatar || !avatarUrl">
                  <span v-if="loadingAvatar" class="spinner-border spinner-border-sm me-1"></span>
                  Supprimer
                </button>
              </div>
              <p class="text-muted small mt-2 mb-0">PNG, JPG, WebP ou GIF &bull; 512 px max &bull; 2 MB max.</p>
            </div>
          </div>
          <div v-if="avatarMsg" :class="['alert mt-3', avatarOk ? 'alert-success' : 'alert-danger']">{{ avatarMsg }}</div>
        </div>
      </div>
    </div>

    <hr class="my-5" />

    <div class="danger-zone p-3 border rounded-3">
      <h4 class="text-danger mb-2"><i class="bi bi-exclamation-triangle-fill me-1"></i> Zone dangereuse</h4>
      <p class="mb-3">
        Supprimer votre compte effacera definitivement vos donnees associees (conversations, messages lies, appareils, etc.). Cette action est irreversible.
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
            <p class="mb-3">Cette action est irreversible. Veuillez saisir votre mot de passe pour confirmer la suppression definitive de votre compte.</p>
            <input v-model="deletePassword" type="password" class="form-control" placeholder="Mot de passe" autocomplete="current-password" />
            <div v-if="deleteError" class="alert alert-danger mt-3">{{ deleteError }}</div>
          </div>
          <div class="custom-modal-footer">
            <button class="btn btn-secondary" @click="closeDeleteModal" :disabled="loadingDelete">Annuler</button>
            <button class="btn btn-danger" @click="confirmDelete" :disabled="!deletePassword || loadingDelete">
              <span v-if="loadingDelete" class="spinner-border spinner-border-sm me-2"></span>
              Supprimer definitivement
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/utils/api'

const avatarUrl = ref(null)
const emailDisplay = ref('')
const DEFAULT_LOCALE = 'fr-BE'
const DEFAULT_TIMEZONE = 'Europe/Brussels'
const formPseudo = ref('')
const formJobTitle = ref('')
const formDepartment = ref('')
const formPhone = ref('')
const formPgp = ref('')
const formStatus = ref('')
const formLocale = ref(DEFAULT_LOCALE)
const formTimezone = ref(DEFAULT_TIMEZONE)
const profileMsg = ref('')
const profileOk = ref(false)
const savingProfile = ref(false)

const localeOptions = [
  { value: 'fr-BE', label: 'Francais (Belgique)' },
  { value: 'fr-FR', label: 'Francais (France)' },
  { value: 'en-GB', label: 'English (UK)' },
  { value: 'en-US', label: 'English (US)' },
]

const timezoneOptions = [
  'Europe/Brussels',
  'Europe/Paris',
  'UTC',
  'America/New_York',
  'Asia/Singapore',
]

const totpEnabled = ref(false)
const totpLockedUntil = ref(null)
const totpLastFailure = ref(null)
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
const loadingAvatar = ref(false)
const avatarMsg = ref('')
const avatarOk = ref(false)
const loadingTotp = ref(false)
const loadingDelete = ref(false)
const deleteError = ref('')
const showDeleteModal = ref(false)
const deletePassword = ref('')

const storedBrowserPref = (() => {
  try { return localStorage.getItem('notif_browser') === '1' }
  catch { return false }
})()

const notifLogin = ref(false)
const notifBrowser = ref(storedBrowserPref)
const secMsg = ref('')
const secMsgType = ref('info')
const emailQuietStart = ref('')
const emailQuietEnd = ref('')
const loadingEmailPref = ref(false)
const emailPrefMsg = ref('')
const emailPrefOk = ref(false)
const sendingTestEmail = ref(false)
const browserSupported = ref(false)
const browserPermission = ref('default')
const browserMsg = ref('')
const browserMsgType = ref('info')
const syncingPushPref = ref(false)
const pushServerAllowed = ref(true)
const preferencesLoaded = ref(false)

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
const avatarInitials = computed(() => {
  const base = (formPseudo.value || '').trim() || (emailDisplay.value || '').trim()
  if (!base) return 'SC'
  const parts = base.replace(/[_\-@.]+/g, ' ').split(/\s+/).filter(Boolean)
  const initials = (parts[0]?.[0] || '') + (parts[1]?.[0] || '')
  const candidate = initials || parts[0]?.slice(0, 2) || base[0]
  return candidate.toUpperCase()
})
const formattedTotpLock = computed(() => {
  if (!totpLockedUntil.value) return null
  try {
    return new Date(totpLockedUntil.value).toLocaleString()
  } catch {
    return totpLockedUntil.value
  }
})

const router = useRouter()

function readStoredBrowserPref() {
  try { return localStorage.getItem('notif_browser') === '1' }
  catch { return false }
}

function writeStoredBrowserPref(enabled) {
  try { localStorage.setItem('notif_browser', enabled ? '1' : '0') }
  catch {}
  try {
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('cova:browser-notifications', { detail: { enabled: !!enabled } }),
      )
    }
  } catch {}
}

function resetBrowserMessage() {
  browserMsg.value = ''
  browserMsgType.value = 'info'
}

function initBrowserDefaults() {
  const isClient = typeof window !== 'undefined'
  browserSupported.value = !!(isClient && 'Notification' in window)
  if (!browserSupported.value) {
    browserPermission.value = 'unsupported'
    notifBrowser.value = false
    writeStoredBrowserPref(false)
    return
  }
  try {
    browserPermission.value = Notification.permission
  } catch {
    browserPermission.value = 'default'
  }
  if (browserPermission.value !== 'granted') {
    notifBrowser.value = false
    writeStoredBrowserPref(false)
  }
}

function refreshBrowserToggle() {
  if (!browserSupported.value) {
    notifBrowser.value = false
    return
  }
  try {
    browserPermission.value = Notification.permission
  } catch {
    browserPermission.value = 'default'
  }
  const stored = readStoredBrowserPref()
  const shouldEnable = stored && pushServerAllowed.value && browserPermission.value === 'granted'
  notifBrowser.value = shouldEnable
  if (!shouldEnable) {
    writeStoredBrowserPref(false)
  }
}

onMounted(async () => {
  initBrowserDefaults()
  await fetchProfile()
  await fetchNotificationPreferences()
  await fetchSecurity()
})

function applyProfileResponse(data) {
  if (!data) return
  emailDisplay.value = data.email || ''
  formPseudo.value = data.display_name || ''
  formJobTitle.value = data.job_title || ''
  formDepartment.value = data.department || ''
  formPhone.value = data.phone_number || ''
  formPgp.value = data.pgp_public_key || ''
  formStatus.value = data.status_message || ''
  formLocale.value = data.locale || DEFAULT_LOCALE
  formTimezone.value = data.timezone || DEFAULT_TIMEZONE
  const rawAvatar = data.avatar_url || null
  const resolvedAvatar = rawAvatar ? `${rawAvatar}?v=${Date.now()}` : null
  avatarUrl.value = resolvedAvatar
  avatarMsg.value = ''
  avatarOk.value = false
  if (resolvedAvatar) {
    localStorage.setItem('avatar_url', resolvedAvatar)
  } else {
    localStorage.removeItem('avatar_url')
  }
  const fallbackName = data.display_name || data.email || 'Utilisateur'
  if (fallbackName) {
    localStorage.setItem('pseudo', fallbackName)
  } else {
    localStorage.removeItem('pseudo')
  }
}

async function fetchProfile() {
  try {
    const res = await api.get(`/me/profile`)
    applyProfileResponse(res.data)
    profileMsg.value = ''
    profileOk.value = false
  } catch (e) {
    profileOk.value = false
    profileMsg.value = "Impossible de charger le profil."
  }
}

function normalizeField(value) {
  if (value === null || value === undefined) return null
  if (typeof value !== 'string') return null
  const trimmed = value.trim()
  return trimmed ? trimmed : null
}

async function saveProfile() {
  profileMsg.value = ''
  profileOk.value = false
  savingProfile.value = true
  const payload = {
    display_name: normalizeField(formPseudo.value),
    locale: normalizeField(formLocale.value),
    timezone: normalizeField(formTimezone.value),
    job_title: normalizeField(formJobTitle.value),
    department: normalizeField(formDepartment.value),
    phone_number: normalizeField(formPhone.value),
    pgp_public_key: normalizeField(formPgp.value),
    status_message: normalizeField(formStatus.value),
  }
  try {
    const res = await api.put(`/me/profile`, payload)
    applyProfileResponse(res.data)
    profileOk.value = true
    profileMsg.value = 'Profil mis a jour'
  } catch (e) {
    profileOk.value = false
    profileMsg.value = e?.response?.data?.detail || e?.response?.data?.message || 'Erreur mise a jour du profil'
  } finally {
    savingProfile.value = false
  }
}

async function fetchSecurity() {
  try {
    const res = await api.get(`/me/security`)
    totpEnabled.value = !!res.data.totp_enabled
    notifLogin.value = !!res.data.notification_login
    totpLockedUntil.value = res.data.totp_locked_until || null
    totpLastFailure.value = res.data.last_totp_failure_at || null
    totpStep.value = totpEnabled.value ? 3 : 1
  } catch (e) {
    totpEnabled.value = false
  }
}

async function fetchNotificationPreferences() {
  try {
    const res = await api.get(`/notifications/preferences`)
    const prefs = Array.isArray(res.data) ? res.data : []
    const emailPref = prefs.find(item => item?.channel === 'email')
    if (emailPref && emailPref.quiet_hours) {
      emailQuietStart.value = emailPref.quiet_hours.start || ''
      emailQuietEnd.value = emailPref.quiet_hours.end || ''
    } else if (emailPref) {
      emailQuietStart.value = ''
      emailQuietEnd.value = ''
    } else if (!emailPref) {
      emailQuietStart.value = ''
      emailQuietEnd.value = ''
    }
    const pushPref = prefs.find(item => item?.channel === 'push')
    const remotePushEnabled = pushPref ? !!pushPref.is_enabled : false
    pushServerAllowed.value = remotePushEnabled
    writeStoredBrowserPref(remotePushEnabled)
    preferencesLoaded.value = true
  } catch (e) {
    pushServerAllowed.value = true
    preferencesLoaded.value = true
  } finally {
    refreshBrowserToggle()
  }
}

function getQuietHours(strict = false) {
  const start = (emailQuietStart.value || '').trim()
  const end = (emailQuietEnd.value || '').trim()
  if (!start && !end) return null
  if (!start || !end) {
    if (strict) {
      throw new Error('quiet-hours-incomplete')
    }
    return null
  }
  return {
    start,
    end,
    timezone: formTimezone.value || DEFAULT_TIMEZONE,
  }
}

async function updateEmailPreference({ silent = false, allowPartial = true } = {}) {
  if (!preferencesLoaded.value && silent) return

  let quietHours
  try {
    quietHours = getQuietHours(!allowPartial)
  } catch {
    if (!silent) {
      emailPrefOk.value = false
      emailPrefMsg.value = 'Renseignez les heures de debut et de fin ou laissez les champs vides.'
    }
    return
  }

  if (!silent) {
    emailPrefMsg.value = ''
    emailPrefOk.value = false
    loadingEmailPref.value = true
  }
  try {
    await api.put(`/notifications/preferences/email`, {
      is_enabled: !!notifLogin.value,
      quiet_hours: quietHours,
    })
    if (!silent) {
      emailPrefOk.value = true
      emailPrefMsg.value = 'Preferences e-mail mises a jour.'
    }
  } catch (e) {
    if (!silent) {
      emailPrefOk.value = false
      emailPrefMsg.value = e?.response?.data?.detail || 'Impossible de mettre a jour les alertes e-mail.'
    }
  } finally {
    if (!silent) {
      loadingEmailPref.value = false
    }
  }
}

async function saveEmailPreference() {
  await updateEmailPreference({ silent: false, allowPartial: false })
}

async function sendLoginAlertTest() {
  emailPrefMsg.value = ''
  emailPrefOk.value = false
  if (!notifLogin.value) {
    emailPrefMsg.value = "Activez d'abord l'alerte de connexion pour envoyer un e-mail de test."
    emailPrefOk.value = false
    return
  }
  if (sendingTestEmail.value) return
  sendingTestEmail.value = true
  try {
    const { data } = await api.post(`/notifications/test/login-alert`)
    emailPrefOk.value = true
    emailPrefMsg.value = data?.detail || (data?.skipped
      ? 'Aucune alerte envoyée : plage silencieuse active.'
      : 'E-mail de test programmé. Vérifiez votre messagerie.')
    setTimeout(() => { emailPrefMsg.value = '' }, 5000)
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.response?.data?.error || ''
    if (typeof detail === 'string' && detail.toLowerCase().includes('impossible de programmer le test')) {
      emailPrefOk.value = true
      emailPrefMsg.value = 'E-mail de test envoyé. Ignorez l’avertissement si vous recevez bien la notification.'
      setTimeout(() => { emailPrefMsg.value = '' }, 5000)
    } else {
      emailPrefOk.value = false
      emailPrefMsg.value = detail || 'Impossible de programmer un test actuellement.'
    }
  } finally {
    sendingTestEmail.value = false
  }
}

async function syncPushPreference(enabled) {
  try {
    syncingPushPref.value = true
    await api.put(`/notifications/preferences/push`, {
      is_enabled: !!enabled,
      quiet_hours: null,
    })
    pushServerAllowed.value = !!enabled
    writeStoredBrowserPref(!!enabled)
  } catch (e) {
    // silencieux : le serveur peut ne pas encore supporter la preference push
  } finally {
    syncingPushPref.value = false
    refreshBrowserToggle()
  }
}

function resetPasswordFields() {
  oldPassword.value = ''
  newPassword.value = ''
  newPassword2.value = ''
  pwdModalMsg.value = ''
  pwdModalOk.value = true
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

async function changePassword() {
  pwdModalMsg.value = ''
  pwdMsg.value = ''
  if (!oldPassword.value || !newPassword.value || newPassword.value !== newPassword2.value) {
    pwdModalOk.value = false
    pwdModalMsg.value = 'Verifiez les champs renseignes'
    return
  }
  savingPwd.value = true
  try {
    await api.put(`/me/password`, { old_password: oldPassword.value, new_password: newPassword.value })
    pwdOk.value = true
    pwdMsg.value = 'Mot de passe mis a jour'
    pwdModalOk.value = true
    pwdModalMsg.value = 'Mot de passe mis a jour'
    setTimeout(() => {
      showPasswordModal.value = false
      resetPasswordFields()
    }, 600)
  } catch (e) {
    pwdOk.value = false
    const detail = e.response?.data?.error || e.response?.data?.detail || 'Erreur mise a jour mot de passe'
    pwdMsg.value = ''
    pwdModalOk.value = false
    pwdModalMsg.value = detail
  } finally { savingPwd.value = false }
}

async function saveSecurity() {
  try {
    const res = await api.put(`/me/security`, { notification_login: notifLogin.value })
    notifLogin.value = !!res.data.notification_login
    if (preferencesLoaded.value) {
      await updateEmailPreference({ silent: true, allowPartial: true })
    }
    secMsgType.value = 'success'
    secMsg.value = 'Parametres de securite enregistres'
    setTimeout(() => {
      secMsg.value = ''
    }, 1800)
  } catch (e) {
    notifLogin.value = !notifLogin.value
    secMsgType.value = 'error'
    secMsg.value = e?.response?.data?.detail || "Impossible d'enregistrer vos alertes. Reessayez."
  }
}

async function toggleBrowserNotifications() {
  resetBrowserMessage()
  if (!browserSupported.value) {
    notifBrowser.value = false
    writeStoredBrowserPref(false)
    browserMsgType.value = 'error'
    browserMsg.value = 'Les notifications navigateur ne sont pas disponibles sur ce poste.'
    return
  }

  try {
    browserPermission.value = Notification.permission
  } catch {
    browserPermission.value = 'default'
  }

  if (notifBrowser.value) {
    if (browserPermission.value === 'granted') {
      writeStoredBrowserPref(true)
      await syncPushPreference(true)
      browserMsgType.value = 'success'
      browserMsg.value = 'Notifications navigateur activees sur cet appareil.'
      return
    }
    try {
      const permission = await Notification.requestPermission()
      browserPermission.value = permission
      if (permission === 'granted') {
        notifBrowser.value = true
        writeStoredBrowserPref(true)
        await syncPushPreference(true)
        browserMsgType.value = 'success'
        browserMsg.value = 'Notifications navigateur activees sur cet appareil.'
      } else {
        notifBrowser.value = false
        writeStoredBrowserPref(false)
        await syncPushPreference(false)
        browserMsgType.value = 'error'
        browserMsg.value = permission === 'denied'
          ? 'Autorisez les notifications dans votre navigateur pour recevoir les alertes instantanees.'
          : 'Activation des notifications annulee.'
      }
    } catch (e) {
      notifBrowser.value = false
      writeStoredBrowserPref(false)
      await syncPushPreference(false)
      browserMsgType.value = 'error'
      browserMsg.value = "Impossible de demander l'autorisation de notification."
    }
  } else {
    writeStoredBrowserPref(false)
    await syncPushPreference(false)
    browserMsgType.value = 'info'
    browserMsg.value = 'Notifications navigateur desactivees pour cet appareil.'
  }
}

function testNotification() {
  resetBrowserMessage()
  if (!browserSupported.value) {
    browserMsgType.value = 'error'
    browserMsg.value = 'Ce navigateur ne supporte pas les notifications locales.'
    return
  }
  try {
    browserPermission.value = Notification.permission
  } catch {
    browserPermission.value = 'default'
  }
  if (!notifBrowser.value || browserPermission.value !== 'granted') {
    browserMsgType.value = 'warning'
    browserMsg.value = 'Activez les notifications et autorisez-les dans votre navigateur pour lancer un test.'
    return
  }
  try {
    const n = new Notification('COVA Messagerie', { body: 'Notification test : vous recevrez les nouveaux messages en temps reel.' })
    setTimeout(() => n.close(), 3000)
    browserMsgType.value = 'success'
    browserMsg.value = 'Notification test envoyee sur cet appareil.'
  } catch (e) {
    browserMsgType.value = 'error'
    browserMsg.value = 'Impossible de generer une notification test.'
  }
}

async function uploadAvatar(event) {
  const file = event.target.files?.[0]
  if (!file) return
  avatarMsg.value = ''
  avatarOk.value = false
  if (file.size > 2_000_000) {
    avatarMsg.value = 'Image trop volumineuse (max 2 MB).'
    return
  }
  loadingAvatar.value = true
  const formData = new FormData()
  formData.append('avatar', file)
  try {
    const res = await api.post(`/me/avatar`, formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    const url = res.data.avatar_url ? `${res.data.avatar_url}?v=${Date.now()}` : null
    avatarUrl.value = url
    if (url) {
      localStorage.setItem('avatar_url', url)
    } else {
      localStorage.removeItem('avatar_url')
    }
    avatarOk.value = true
    avatarMsg.value = 'Avatar mis a jour.'
  } catch (e) {
    avatarOk.value = false
    avatarMsg.value = e.response?.data?.detail || e.response?.data?.error || "Impossible de televerser l'image."
  } finally {
    loadingAvatar.value = false
    event.target.value = ''
  }
}

async function deleteAvatar() {
  avatarMsg.value = ''
  avatarOk.value = false
  loadingAvatar.value = true
  try {
    await api.delete(`/me/avatar`)
    avatarUrl.value = null
    localStorage.removeItem('avatar_url')
    avatarOk.value = true
    avatarMsg.value = 'Avatar supprime.'
  } catch (e) {
    avatarOk.value = false
    avatarMsg.value = e.response?.data?.detail || e.response?.data?.error || "Suppression impossible pour le moment."
  } finally {
    loadingAvatar.value = false
  }
}

async function startActivation() {
  totpError.value = ''
  totpSuccess.value = ''
  loadingTotp.value = true
  recoveryCodes.value = []
  try {
    const res = await api.post(`/auth/totp/activate`)
    totpEnrollment.secret = res.data.secret
    totpEnrollment.qr = `data:image/png;base64,${res.data.qr_code}`
    totpEnrollment.provisioningUri = res.data.provisioning_uri
    totpStep.value = 2
  } catch (e) {
    const detail = e.response?.data?.detail || e.message
    totpError.value = detail || 'Erreur lors de la generation du QR code.'
  } finally {
    loadingTotp.value = false
  }
}

async function confirmTotp() {
  totpError.value = ''
  totpSuccess.value = ''
  if (!totpCode.value || totpCode.value.length !== 6) {
    totpError.value = 'Veuillez saisir le code a 6 chiffres genere par votre application.'
    return
  }
  loadingTotp.value = true
  try {
    const res = await api.post(`/auth/totp/confirm`, { code: totpCode.value })
    totpEnabled.value = true
    totpSuccess.value = res.data.message || 'Double authentification activee.'
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

async function deactivateTotp() {
  if (!window.confirm('Souhaitez-vous desactiver la double authentification ?')) return
  totpError.value = ''
  totpSuccess.value = ''
  loadingTotp.value = true
  try {
    const res = await api.post(`/auth/totp/deactivate`)
    totpEnabled.value = false
    totpSuccess.value = res.data.message || 'Double authentification desactivee.'
    totpEnrollment.secret = ''
    totpEnrollment.qr = ''
    totpEnrollment.provisioningUri = ''
    totpCode.value = ''
    recoveryCodes.value = []
    totpStep.value = 1
    await fetchSecurity()
  } catch (e) {
    const detail = e.response?.data?.detail || e.response?.data?.error || e.message
    totpError.value = detail || 'Impossible de desactiver la double authentification pour le moment.'
  } finally {
    loadingTotp.value = false
  }
}

function openRecoveryModal() {
  if (recoveryCodes.value.length > 0) {
    showRecoveryModal.value = true
  }
}
function closeRecoveryModal() { showRecoveryModal.value = false }

function downloadRecoveryCodes() {
  if (!recoveryCodes.value.length) return
  const content = [
    'Codes de recuperation COVA',
    '-------------------------',
    ...recoveryCodes.value,
    '',
    'Conservez ces codes en lieu sur.',
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
    totpSuccess.value = 'Copie dans le presse-papiers.'
    setTimeout(() => { totpSuccess.value = '' }, 1500)
  } catch {
    totpError.value = 'Impossible de copier automatiquement.'
  }
}
function openDeleteModal() {
  deleteError.value = ''
  deletePassword.value = ''
  showDeleteModal.value = true
}
function closeDeleteModal() {
  if (!loadingDelete.value) showDeleteModal.value = false
}
async function confirmDelete() {
  deleteError.value = ''
  loadingDelete.value = true
  try {
    await api.delete(`/me`, { data: { password: deletePassword.value } })
    localStorage.clear(); router.push('/login')
  } catch (e) {
    deleteError.value = e.response?.data?.detail || e.response?.data?.error || 'Suppression impossible pour le moment.'
  } finally { loadingDelete.value = false }
}
</script>

<style scoped>
.avatar-settings { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px 16px; }
.avatar-preview-wrapper { width: 64px; height: 64px; }
.avatar-preview,
.avatar-placeholder { width: 64px; height: 64px; border-radius: 50%; object-fit: cover; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #1d4ed8, #0f172a); color: #fff; font-weight: 600; letter-spacing: .05em; }
.avatar-placeholder { font-size: 1rem; text-transform: uppercase; }
.avatar-input { max-width: 240px; min-width: 180px; }
.danger-zone { background: #fffaf9 }
.danger-zone { background: #fffaf9 }

.totp-card {
  background: linear-gradient(135deg, #f8fbff 0%, #eef4ff 100%);
  border: 1px solid #dbeafe;
  border-radius: 1rem;
  padding: 1.5rem;
  color: #0f172a;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
}
.totp-card p {
  color: #334155;
}
.totp-steps {
  list-style: decimal;
  padding-left: 1.2rem;
  color: #475569;
}
.totp-steps li {
  margin-bottom: .35rem;
}
.totp-steps li.active {
  color: #2563eb;
  font-weight: 600;
}
.totp-enrollment {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  padding: 1.25rem;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.08);
}
.totp-qr {
  width: 140px;
  height: 140px;
  border-radius: .75rem;
  background: #fff;
  padding: .75rem;
  box-shadow: 0 10px 30px rgba(15, 23, 42, .12);
}
.copyable-field button { border-top-left-radius: 0; border-bottom-left-radius: 0; }
.totp-uri {
  background: #f8fafc;
  border-radius: .75rem;
  padding: .75rem 1rem;
  font-size: .75rem;
  overflow-x: auto;
  color: #1f2937;
  border: 1px dashed #cbd5f5;
}
.recovery-list { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: .35rem; padding-left: 0; list-style: none; }
.recovery-list li { background: #f1f5f9; border: 1px solid #dbeafe; border-radius: .75rem; padding: .6rem .8rem; font-family: 'Fira Code', 'Courier New', monospace; font-size: .85rem; letter-spacing: .08em; text-align: center; color: #0f172a; }

/* Modal custom leger base sur Bootstrap */
.custom-modal { position: fixed; top: 0; left: 0; right:0; bottom:0; display:flex; align-items:center; justify-content:center; z-index: 1050; }
.custom-modal-dialog { max-width: 520px; width: 92%; }
.custom-modal-content { background: #fff; border-radius: .75rem; box-shadow: 0 12px 40px rgba(0,0,0,.15); overflow: hidden; }
.custom-modal-header { display:flex; align-items:center; justify-content:space-between; padding: .85rem 1rem; border-bottom: 1px solid #eee; }
.custom-modal-title { margin: 0; }
.custom-modal-body { padding: 1rem; }
.custom-modal-footer { display:flex; gap:.5rem; justify-content:flex-end; padding: .85rem 1rem; border-top: 1px solid #eee; }
.modal-backdrop.show { opacity: .25; }

@media (max-width: 576px) {
  .avatar-settings { flex-direction: column; align-items: flex-start !important; }
  .avatar-preview-wrapper { margin-bottom: .75rem; }
  .avatar-input { width: 100%; min-width: 0; }
}
</style>




















