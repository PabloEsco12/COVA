<template>
  <div class="card p-3 h-100">
    <h4 class="mb-3">Profil</h4>

    <div class="mb-3">
      <label class="form-label">Adresse e-mail</label>
      <input class="form-control" :value="emailDisplay" disabled />
    </div>

    <div class="mb-3">
      <label class="form-label">Nom d'affichage</label>
      <input
        v-model.trim="formPseudo"
        class="form-control"
        placeholder="Nom visible par vos interlocuteurs"
      />
    </div>

    <div class="row g-2">
      <div class="col-md-6">
        <label class="form-label">Fonction</label>
        <input
          v-model.trim="formJobTitle"
          class="form-control"
          placeholder="Ex. Responsable Securite"
        />
      </div>
      <div class="col-md-6">
        <label class="form-label">Département / Équipe</label>
        <input
          v-model.trim="formDepartment"
          class="form-control"
          placeholder="Ex. SOC Europe"
        />
      </div>
    </div>

    <div class="row g-2 mt-2">
      <div class="col-md-6">
        <label class="form-label">Numéro de téléphone sécurisé</label>
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
        <label class="form-label">Langue préférée</label>
        <select v-model="formLocale" class="form-select">
          <option v-for="loc in localeOptions" :key="loc.value" :value="loc.value">
            {{ loc.label }}
          </option>
        </select>
      </div>
      <div class="col-md-6">
        <label class="form-label">Message d'état</label>
        <input
          v-model.trim="formStatus"
          class="form-control"
          placeholder="Disponible, en deplacement…"
        />
      </div>
    </div>

    <div class="mt-3">
      <label class="form-label">Clé publique PGP (optionnel)</label>
      <textarea
        v-model.trim="formPgp"
        class="form-control"
        rows="3"
        placeholder="-----BEGIN PGP PUBLIC KEY BLOCK-----"
      ></textarea>
    </div>

    <div class="d-flex justify-content-end mt-3">
      <button class="btn btn-outline-primary" @click="saveProfile" :disabled="savingProfile">
        <span v-if="savingProfile" class="spinner-border spinner-border-sm"></span>
        <span v-else>Enregistrer le profil</span>
      </button>
    </div>

    <div
      v-if="profileMsg"
      :class="['alert mt-3', profileOk ? 'alert-success' : 'alert-danger']"
    >
      {{ profileMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api, backendBase } from '@/utils/api'
import { broadcastProfileUpdate, normalizeAvatarUrl } from '@/utils/profile'

const emit = defineEmits(['profile-loaded', 'profile-updated'])

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

onMounted(fetchProfile)

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

  // on signale au parent (pour l’avatar par ex.)
  const normalizedAvatar = normalizeAvatarUrl(data.avatar_url, {
    baseUrl: backendBase,
    cacheBust: true,
  })
  const payload = {
    email: data.email || '',
    display_name: data.display_name || '',
    avatar_url: normalizedAvatar,
    status_message: data.status_message || '',
  }
  emit('profile-loaded', payload)
  broadcastProfileUpdate(payload)
}

async function fetchProfile() {
  try {
    const res = await api.get('/me/profile')
    applyProfileResponse(res.data)
    profileMsg.value = ''
    profileOk.value = false
  } catch (e) {
    profileOk.value = false
    profileMsg.value = 'Impossible de charger le profil.'
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
    const res = await api.put('/me/profile', payload)
    applyProfileResponse(res.data)
    profileOk.value = true
    profileMsg.value = 'Profil mis à jour'
    const normalizedAvatar = normalizeAvatarUrl(res.data.avatar_url, {
      baseUrl: backendBase,
      cacheBust: true,
    })
    const payloadUpdate = {
      email: res.data.email,
      display_name: res.data.display_name,
      avatar_url: normalizedAvatar,
      status_message: res.data.status_message || '',
    }
    emit('profile-updated', payloadUpdate)
    broadcastProfileUpdate(payloadUpdate)
  } catch (e) {
    profileOk.value = false
    profileMsg.value =
      e?.response?.data?.detail ||
      e?.response?.data?.message ||
      'Erreur mise à jour du profil'
  } finally {
    savingProfile.value = false
  }
}

</script>
<style scoped src="@/assets/styles/settings.css"></style>
