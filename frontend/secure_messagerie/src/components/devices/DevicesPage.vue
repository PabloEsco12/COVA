<template>
  <div class="devices-page">
    <DevicesToolbar
      :loading="loading"
      :registering="registering"
      :logout-busy="logoutBusy"
      @logout-everywhere="logoutEverywhere"
      @manual-sync="manualSync"
      @rename-current="openRenameModal"
    />

    <DevicesSummary v-if="deviceCards.length" :summary="summary" />

    <div v-if="error" class="alert alert-danger d-flex align-items-center gap-2">
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{{ error }}</span>
    </div>
    <div v-if="success" class="alert alert-success d-flex align-items-center gap-2">
      <i class="bi bi-check-circle-fill"></i>
      <span>{{ success }}</span>
    </div>

    <div v-if="loading" class="loader-stack">
      <Spinner />
      <p class="text-muted mt-3">Récupération de vos appareils sécurisés...</p>
    </div>

    <div v-else>
      <DevicesEmptyState
        v-if="!deviceCards.length"
        :registering="registering"
        @manual-sync="manualSync"
      />

      <DevicesGrid
        v-else
        :devices="deviceCards"
        :revoking="revoking"
        @open-details="openDetails"
        @open-delete="openDeleteModal"
      />
    </div>

    <DeviceDetailsModal
      :show="!!detailsModal"
      :device="detailsModal"
      :revoking="revoking"
      @close="detailsModal = null"
      @revoke="confirmDelete"
    />

    <RenameDeviceModal
      :show="showRenameModal"
      :initial-name="renameValue"
      :busy="renameBusy"
      :error="renameError"
      @close="closeRenameModal"
      @confirm="confirmRenameFromModal"
    />

    <DeleteDeviceModal
      :show="showDeleteModal"
      :device="deleteTarget"
      :busy="deleteBusy"
      :error="deleteError"
      @close="closeDeleteModal"
      @confirm="confirmDelete"
    />
  </div>
</template>

<script setup>
/*
  Composant reconstitué pour coller au résultat de ton ancien Devices.vue
  - GET /me/devices  --> { devices: [...] }
  - POST /me/devices --> { device_id, push_token, platform }
  - toutes les fonctions utilitaires sont dans CE fichier
*/

import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { api } from '@/utils/api'

import Spinner from '@/components/confirm/Spinner.vue'
import DevicesToolbar from '@/components/devices/DevicesToolbar.vue'
import DevicesSummary from '@/components/devices/DevicesSummary.vue'
import DevicesEmptyState from '@/components/devices/DevicesEmptyState.vue'
import DevicesGrid from '@/components/devices/DevicesGrid.vue'
import DeviceDetailsModal from '@/components/devices/DeviceDetailsModal.vue'
import RenameDeviceModal from '@/components/devices/RenameDeviceModal.vue'
import DeleteDeviceModal from '@/components/devices/DeleteDeviceModal.vue'

/* -------------------------------------------------------------------------- */
/* state                                                                      */
/* -------------------------------------------------------------------------- */
const devices = ref([])
const loading = ref(true)
const error = ref('')
const success = ref('')
const registering = ref(false)
const logoutBusy = ref(false)
const revoking = ref('')

const detailsModal = ref(null)
const showRenameModal = ref(false)
const renameValue = ref('')
const renameBusy = ref(false)
const renameError = ref('')

const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const deleteBusy = ref(false)
const deleteError = ref('')

const deviceLabelKey = 'cova_device_label'
const localDeviceId = ref('')
let successTimer = null
let autoRegistrationTried = false

/* -------------------------------------------------------------------------- */
/* computed                                                                   */
/* -------------------------------------------------------------------------- */
const currentDevicePresent = computed(() =>
  devices.value.some((d) => d.id === localDeviceId.value),
)

const deviceCards = computed(() =>
  devices.value
    .map(transformDevice)
    .sort((a, b) => {
      if (a.isCurrent && !b.isCurrent) return -1
      if (!a.isCurrent && b.isCurrent) return 1
      return new Date(b.rawCreatedAt).getTime() - new Date(a.rawCreatedAt).getTime()
    }),
)

const summary = computed(() => buildSummary(deviceCards.value))

/* -------------------------------------------------------------------------- */
/* lifecycle                                                                  */
/* -------------------------------------------------------------------------- */
onMounted(async () => {
  localDeviceId.value = ensureLocalDeviceId()
  await init()
})

onBeforeUnmount(() => {
  if (successTimer) {
    clearTimeout(successTimer)
    successTimer = null
  }
})

/* -------------------------------------------------------------------------- */
/* main logic                                                                 */
/* -------------------------------------------------------------------------- */
async function init() {
  loading.value = true
  error.value = ''
  try {
    await loadDevices()

    // si l'appareil actuel n'est pas dans la liste → faire comme avant : 1 sync auto
    if (!currentDevicePresent.value && !autoRegistrationTried) {
      autoRegistrationTried = true
      await manualSync()
    }
  } catch (err) {
    const status = err?.response?.status
    if (status === 401) {
      error.value = 'Session expirée ou non authentifiée.'
    } else {
      error.value = extractError(err, 'Impossible de récupérer vos appareils.')
    }
  } finally {
    loading.value = false
  }
}

async function loadDevices() {
  // IMPORTANT : ton backend renvoie { devices: [...] }
  const { data } = await api.get('/me/devices')
  devices.value = Array.isArray(data?.devices) ? data.devices : []
}

async function manualSync() {
  try {
    await syncCurrentDevice()
    await loadDevices()
  } catch (err) {
    const status = err?.response?.status
    if (status === 401) return
    error.value = extractError(err, "Impossible de synchroniser l'appareil.")
  }
}

async function syncCurrentDevice() {
  if (!localDeviceId.value) {
    localDeviceId.value = ensureLocalDeviceId()
  }
  const meta = buildMetadata()
  const label = safeGetLocal(deviceLabelKey)
  if (label) {
    meta.label = label
  }

  const pushToken = encodeMetadata(meta)

  registering.value = true
  error.value = ''

  try {
    await api.post('/me/devices', {
      device_id: localDeviceId.value,
      push_token: pushToken,
      platform: mapDeviceTypeToPlatform(meta.deviceType),
    })
    setSuccessMessage('Appareil synchronisé.')
  } finally {
    registering.value = false
  }
}

/* -------------------------------------------------------------------------- */
/* UI actions                                                                 */
/* -------------------------------------------------------------------------- */
function openDetails(device) {
  detailsModal.value = device
}

function openRenameModal() {
  renameError.value = ''
  renameValue.value =
    safeGetLocal(deviceLabelKey) ||
    deviceCards.value.find((d) => d.isCurrent)?.label ||
    detectDefaultLabel({})
  showRenameModal.value = true
  nextTick(() => {})
}

function closeRenameModal() {
  if (renameBusy.value) return
  showRenameModal.value = false
}

async function confirmRenameFromModal(nextLabel) {
  renameValue.value = nextLabel
  await confirmRename()
}

async function confirmRename() {
  renameError.value = ''
  const nextLabel = (renameValue.value || '').trim().slice(0, 60)
  if (!nextLabel) {
    renameError.value = 'Veuillez saisir un nom compréhensible.'
    return
  }
  renameBusy.value = true
  try {
    safeSetLocal(deviceLabelKey, nextLabel)
    await manualSync()
    showRenameModal.value = false
    setSuccessMessage("Nom de l'appareil mis à jour.")
  } catch (err) {
    renameError.value = extractError(err, "Impossible de renommer cet appareil.")
  } finally {
    renameBusy.value = false
  }
}

function openDeleteModal(device) {
  deleteTarget.value = device
  deleteError.value = ''
  showDeleteModal.value = true
}

function closeDeleteModal() {
  if (deleteBusy.value) return
  showDeleteModal.value = false
  deleteTarget.value = null
}

async function confirmDelete(deviceOverride) {
  const target = deviceOverride || deleteTarget.value
  if (!target || deleteBusy.value) return
  if (!target.id) {
    deleteError.value = "Identifiant de l'appareil indisponible."
    return
  }

  deleteBusy.value = true
  deleteError.value = ''
  revoking.value = target.id

  try {
    await api.delete(`/me/devices/${encodeURIComponent(target.id)}`)
    showDeleteModal.value = false
    deleteTarget.value = null
    setSuccessMessage('Appareil déconnecté.')
    await loadDevices()
  } catch (err) {
    const status = err?.response?.status
    if (status === 401) return
    deleteError.value = extractError(err, "Impossible de déconnecter cet appareil.")
  } finally {
    deleteBusy.value = false
    revoking.value = ''
  }
}

async function logoutEverywhere() {
  logoutBusy.value = true
  error.value = ''
  try {
    await api.post('/auth/logout-all')
    setSuccessMessage('Toutes les sessions sont invalidées.')
    await loadDevices()
  } catch (err) {
    error.value = extractError(err, 'Impossible de déconnecter les autres appareils.')
  } finally {
    logoutBusy.value = false
  }
}

/* -------------------------------------------------------------------------- */
/* helpers d’affichage                                                        */
/* -------------------------------------------------------------------------- */
function setSuccessMessage(msg) {
  success.value = msg
  if (successTimer) clearTimeout(successTimer)
  successTimer = setTimeout(() => {
    success.value = ''
    successTimer = null
  }, 3500)
}

function transformDevice(raw) {
  const metadata = decodeMetadata(raw.push_token)
  const ua = metadata.userAgent || metadata.ua || ''
  const browser = metadata.browser || detectBrowser(ua)
  const os = metadata.os || detectOs(ua)
  const deviceType = metadata.deviceType || detectDeviceType(ua) || convertPlatformToType(raw.platform)
  const label = trimLabel(metadata.label || detectDefaultLabel({ browser, os }))
  const subtitle = buildSubtitle(browser, os)
  const screen = metadata.screen || metadata.screenSize || ''
  const timezone = metadata.timezone || metadata.tz || ''
  const language = metadata.language || metadata.lang || ''
  const lastSync = metadata.syncedAt ? formatDate(metadata.syncedAt) : ''
  const lastSeenAt = raw.last_seen_at ? formatDate(raw.last_seen_at) : ''
  const lastSeenRelative = formatRelative(raw.last_seen_at)
  const trustLevel = Number.isFinite(raw.trust_level) ? Math.min(Math.max(raw.trust_level, 0), 100) : 0
  const trustInfo = mapTrust(trustLevel)
  const iconData = pickIcon(deviceType)

  return {
    id: raw.id,
    recordId: raw.record_id,
    rawCreatedAt: raw.created_at,
    createdAt: formatDate(raw.created_at),
    lastSeenAt,
    lastSeenRelative,
    trustLevel,
    trustVariant: trustInfo.variant,
    trustLabel: trustInfo.label,
    trustIcon: trustInfo.icon,
    isCurrent: raw.id === localDeviceId.value,
    label,
    subtitle,
    timezone,
    language,
    screen,
    lastSync,
    metadata,
    icon: iconData.icon,
    iconClass: iconData.iconClass,
  }
}

function buildSubtitle(browser, os) {
  const parts = []
  if (browser) parts.push(browser)
  if (os) parts.push(os)
  return parts.join(' · ')
}

function buildSummary(list) {
  const total = list.length
  const risky = list.filter((d) => d.trustVariant === 'watch' || d.trustVariant === 'alert').length
  const current = list.find((d) => d.isCurrent)
  const lastSeen = list
    .filter((d) => d.lastSeenAt)
    .sort((a, b) => new Date(b.lastSeenAt).getTime() - new Date(a.lastSeenAt).getTime())[0]

  return {
    total,
    risky,
    lastSeenAt: lastSeen?.lastSeenAt || '',
    lastSeenRelative: lastSeen?.lastSeenRelative || '',
    currentLabel: current ? `Cet appareil · ${current.label}` : 'Aucun appareil local détecté',
  }
}

/* -------------------------------------------------------------------------- */
/* utils metadata                                                             */
/* -------------------------------------------------------------------------- */
function buildMetadata() {
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : ''
  const lang = typeof navigator !== 'undefined' ? navigator.language : ''
  const tz = typeof Intl !== 'undefined' ? Intl.DateTimeFormat().resolvedOptions().timeZone : ''
  const screenSize =
    typeof window !== 'undefined' ? `${window.screen.width}x${window.screen.height}` : undefined
  const deviceType = detectDeviceType(ua)

  return {
    userAgent: ua || undefined,
    language: lang || undefined,
    timezone: tz || undefined,
    screen: screenSize || undefined,
    deviceType: deviceType || undefined,
    syncedAt: new Date().toISOString(),
  }
}

function encodeMetadata(obj) {
  try {
    return toBase64(JSON.stringify(obj))
  } catch {
    return ''
  }
}

function decodeMetadata(value) {
  if (!value) return {}
  try {
    const json = fromBase64(value)
    const data = JSON.parse(json)
    return data && typeof data === 'object' ? data : {}
  } catch {
    return {}
  }
}

/* -------------------------------------------------------------------------- */
/* utils navigateur / device                                                  */
/* -------------------------------------------------------------------------- */
function detectBrowser(ua = '') {
  ua = (ua || '').toLowerCase()
  if (!ua) return ''
  if (ua.includes('chrome') && !ua.includes('edge') && !ua.includes('opr')) return 'Chrome'
  if (ua.includes('safari') && !ua.includes('chrome')) return 'Safari'
  if (ua.includes('firefox')) return 'Firefox'
  if (ua.includes('edg')) return 'Edge'
  if (ua.includes('opr') || ua.includes('opera')) return 'Opera'
  return ''
}

function detectOs(ua = '') {
  ua = (ua || '').toLowerCase()
  if (!ua) return ''
  if (ua.includes('windows')) return 'Windows'
  if (ua.includes('mac os') || ua.includes('macos')) return 'macOS'
  if (ua.includes('android')) return 'Android'
  if (ua.includes('iphone') || ua.includes('ipad') || ua.includes('ios')) return 'iOS'
  if (ua.includes('linux')) return 'Linux'
  return ''
}

function detectDeviceType(ua = '') {
  ua = (ua || '').toLowerCase()
  if (/mobile|iphone|android(?!.*tablet)/.test(ua)) return 'mobile'
  if (/ipad|tablet/.test(ua)) return 'tablet'
  if (/smart-tv|smarttv|hbbtv/.test(ua)) return 'tv'
  return 'desktop'
}

function convertPlatformToType(platform) {
  if (!platform) return 'desktop'
  const p = platform.toLowerCase()
  if (p.includes('ios') || p.includes('android')) return 'mobile'
  if (p.includes('ipad') || p.includes('tablet')) return 'tablet'
  return 'desktop'
}

function pickIcon(deviceType) {
  switch (deviceType) {
    case 'mobile':
      return { icon: 'bi bi-phone', iconClass: 'device-avatar--mobile' }
    case 'tablet':
      return { icon: 'bi bi-tablet-landscape', iconClass: 'device-avatar--tablet' }
    case 'tv':
      return { icon: 'bi bi-tv', iconClass: 'device-avatar--tv' }
    default:
      return { icon: 'bi bi-laptop', iconClass: 'device-avatar--desktop' }
  }
}

function mapDeviceTypeToPlatform(type) {
  switch (type) {
    case 'mobile':
      return 'mobile'
    case 'tablet':
      return 'tablet'
    case 'tv':
      return 'tv'
    case 'bot':
      return 'bot'
    default:
      return 'desktop'
  }
}

/* -------------------------------------------------------------------------- */
/* utils divers                                                               */
/* -------------------------------------------------------------------------- */
function ensureLocalDeviceId() {
  const key = 'cova_device_id'
  if (typeof localStorage === 'undefined') return ''
  let id = localStorage.getItem(key)
  if (!id) {
    id = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).slice(2)
    localStorage.setItem(key, id)
  }
  return id
}

function detectDefaultLabel({ browser, os } = {}) {
  const parts = []
  if (browser) parts.push(browser)
  if (os) parts.push(os)
  if (!parts.length) return 'Appareil'
  return parts.join(' · ')
}

function toBase64(str) {
  if (typeof btoa !== 'undefined') return btoa(str)
  return Buffer.from(str, 'utf-8').toString('base64')
}

function fromBase64(str) {
  if (typeof atob !== 'undefined') return atob(str)
  return Buffer.from(str, 'base64').toString('utf-8')
}

function formatDate(dateLike) {
  if (!dateLike) return ''
  const d = new Date(dateLike)
  return d.toLocaleString('fr-FR', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatRelative(dateLike) {
  if (!dateLike) return ''
  const now = new Date()
  const d = new Date(dateLike)
  const diff = d.getTime() - now.getTime()
  const sec = Math.round(diff / 1000)
  const abs = Math.abs(sec)

  let unit = 'second'
  let value = sec
  if (abs >= 60 && abs < 3600) {
    unit = 'minute'
    value = Math.round(sec / 60)
  } else if (abs >= 3600 && abs < 86400) {
    unit = 'hour'
    value = Math.round(sec / 3600)
  } else if (abs >= 86400 && abs < 604800) {
    unit = 'day'
    value = Math.round(sec / 86400)
  } else if (abs >= 604800) {
    unit = 'week'
    value = Math.round(sec / 604800)
  }

  if (typeof Intl !== 'undefined' && Intl.RelativeTimeFormat) {
    const rtf = new Intl.RelativeTimeFormat('fr-FR', { numeric: 'auto' })
    return rtf.format(value, unit)
  }
  return formatDate(dateLike)
}

function mapTrust(level) {
  if (level >= 80) return { variant: 'trusted', label: 'Fiable', icon: 'bi bi-shield-check' }
  if (level >= 50) return { variant: 'standard', label: 'Normal', icon: 'bi bi-shield' }
  if (level >= 25) return { variant: 'watch', label: 'À surveiller', icon: 'bi bi-exclamation-triangle' }
  return { variant: 'alert', label: 'Risque', icon: 'bi bi-bug' }
}

function trimLabel(str) {
  return (str || '').trim().slice(0, 60)
}

function safeGetLocal(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return ''
  }
}

function safeSetLocal(key, val) {
  try {
    localStorage.setItem(key, val)
  } catch {
    // ignore
  }
}

function extractError(err, fallback = 'Erreur inconnue.') {
  const data = err?.response?.data
  const detail =
    (Array.isArray(data?.detail) && data.detail[0]) || data?.message || data?.error || err?.message
  return detail ? String(detail) : fallback
}
</script>
