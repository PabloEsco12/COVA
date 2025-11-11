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
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import Spinner from '../confirm/Spinner.vue'
import { api } from '../../utils/api'

import DevicesToolbar from './DevicesToolbar.vue'
import DevicesSummary from './DevicesSummary.vue'
import DevicesEmptyState from './DevicesEmptyState.vue'
import DevicesGrid from './DevicesGrid.vue'
import DeviceDetailsModal from './DeviceDetailsModal.vue'
import RenameDeviceModal from './RenameDeviceModal.vue'
import DeleteDeviceModal from './DeleteDeviceModal.vue'

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

const currentDevicePresent = computed(() =>
  devices.value.some((device) => device.id === localDeviceId.value),
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

async function init() {
  loading.value = true
  error.value = ''
  try {
    await loadDevices()

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
  // ⚠️ ton backend renvoie { devices: [...] }
  const { data } = await api.get('/me/devices')
  devices.value = Array.isArray(data?.devices) ? data.devices : []
}

async function manualSync() {
  try {
    await syncCurrentDevice({ silent: false })
    await loadDevices()
  } catch (err) {
    const status = err?.response?.status
    if (status === 401) return
    error.value = extractError(err, "Impossible de synchroniser l'appareil.")
  }
}

async function syncCurrentDevice({ silent } = { silent: false }) {
  if (!localDeviceId.value) {
    localDeviceId.value = ensureLocalDeviceId()
  }
  if (!localDeviceId.value) {
    if (!silent) error.value = "Impossible de générer un identifiant pour cet appareil."
    return
  }

  const meta = buildMetadata()
  const payload = encodeMetadata({ ...meta, deviceId: localDeviceId.value })
  if (!payload) {
    if (!silent) error.value = "Impossible de préparer l'empreinte de cet appareil."
    return
  }

  if (!silent) {
    registering.value = true
    error.value = ''
  }

  try {
    await api.post('/me/devices', {
      device_id: localDeviceId.value,
      push_token: payload,
      platform: mapDeviceTypeToPlatform(meta.deviceType),
    })
    if (!silent) setSuccessMessage('Appareil synchronisé.')
  } catch (err) {
    if (!silent) error.value = extractError(err, "Impossible d'enregistrer cet appareil.")
    throw err
  } finally {
    if (!silent) registering.value = false
  }
}

function openDetails(device) {
  detailsModal.value = device
}

function openRenameModal() {
  const current = deviceCards.value.find((d) => d.isCurrent)
  const stored = safeGetLocal(deviceLabelKey)
  renameValue.value = current?.metadata.label || stored || detectDefaultLabel({})
  renameError.value = ''
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
    showRenameModal.value = false
    await manualSync()
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
  let target = deviceOverride || deleteTarget.value
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
    const msg = extractError(err, "Impossible de déconnecter cet appareil.")
    deleteError.value = msg
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

function setSuccessMessage(message) {
  success.value = message
  if (successTimer) {
    clearTimeout(successTimer)
  }
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

function buildSummary(list) {
  const total = list.length
  const risky = list.filter((d) => d.trustVariant === 'watch' || d.trustVariant === 'alert').length
  const current = list.find((d) => d.isCurrent)
  const lastSeen = list
    .filter((device) => device.lastSeenAt)
    .sort((a, b) => new Date(b.lastSeenAt).getTime() - new Date(a.lastSeenAt).getTime())[0]

  return {
    total,
    risky,
    lastSeenAt: lastSeen?.lastSeenAt || '',
    lastSeenRelative: lastSeen?.lastSeenRelative || '',
    currentLabel: current ? `Cet appareil · ${current.label}` : 'Aucun appareil local détecté',
  }
}

function detectDefaultLabel({ browser, os } = {}) {
  const parts = []
  if (browser) parts.push(browser)
  if (os) parts.push(os)
  if (!parts.length) return 'Appareil'
  return parts.join(' · ')
}

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

function encodeMetadata(meta) {
  try {
    const payload = { ...meta }
    delete payload.raw
    return toBase64(JSON.stringify(payload))
  } catch (err) {
    console.error('encodeMetadata failure', err)
    return ''
  }
}

function decodeMetadata(token) {
  if (!token) return {}
  try {
    const decoded = fromBase64(token)
    const parsed = JSON.parse(decoded)
    if (parsed && typeof parsed === 'object') {
      return { ...parsed, raw: token }
    }
  } catch (err) {
    console.warn('decodeMetadata failure', err)
  }
  return { raw: token }
}

function toBase64(value) {
  if (!value) return ''
  try {
    if (typeof window !== 'undefined' && typeof window.btoa === 'function') {
      return window.btoa(unescape(encodeURIComponent(value)))
    }
    if (typeof globalThis !== 'undefined' && globalThis.Buffer) {
      return globalThis.Buffer.from(value, 'utf-8').toString('base64')
    }
  } catch {}
  return ''
}

function fromBase64(value) {
  if (!value) return ''
  try {
    if (typeof window !== 'undefined' && typeof window.atob === 'function') {
      return decodeURIComponent(
        window
          .atob(value)
          .split('')
          .map((char) => `%${char.charCodeAt(0).toString(16).padStart(2, '0')}`)
          .join(''),
      )
    }
    if (typeof globalThis !== 'undefined' && globalThis.Buffer) {
      return globalThis.Buffer.from(value, 'base64').toString('utf-8')
    }
  } catch {}
  return ''
}

function detectBrowser(ua = '') {
  if (!ua) return ''
  ua = ua.toLowerCase()
  if (ua.includes('chrome') && !ua.includes('edge') && !ua.includes('opr')) return 'Chrome'
  if (ua.includes('safari') && !ua.includes('chrome')) return 'Safari'
  if (ua.includes('firefox')) return 'Firefox'
  if (ua.includes('edg')) return 'Edge'
  if (ua.includes('opr') || ua.includes('opera')) return 'Opera'
  return ''
}

function detectOs(ua = '') {
  if (!ua) return ''
  ua = ua.toLowerCase()
  if (ua.includes('windows')) return 'Windows'
  if (ua.includes('mac os') || ua.includes('macos')) return 'macOS'
  if (ua.includes('android')) return 'Android'
  if (ua.includes('iphone') || ua.includes('ipad') || ua.includes('ios')) return 'iOS'
  if (ua.includes('linux')) return 'Linux'
  return ''
}

function detectDeviceType(ua = '') {
  ua = ua.toLowerCase()
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

function mapTrust(level) {
  if (level >= 80) {
    return { variant: 'trusted', label: 'Fiable', icon: 'bi bi-shield-check' }
  }
  if (level >= 50) {
    return { variant: 'standard', label: 'Normal', icon: 'bi bi-shield' }
  }
  if (level >= 25) {
    return { variant: 'watch', label: 'À surveiller', icon: 'bi bi-exclamation-triangle' }
  }
  return { variant: 'alert', label: 'Risque', icon: 'bi bi-bug' }
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
    case 'desktop':
    default:
      return 'desktop'
  }
}

function trimLabel(value) {
  return (value || '').trim().slice(0, 60)
}

function safeGetLocal(key) {
  try {
    return localStorage.getItem(key)
  } catch {
    return ''
  }
}

function safeSetLocal(key, value) {
  try {
    localStorage.setItem(key, value)
  } catch {
    // ignore
  }
}

function extractError(err, fallback = 'Erreur inconnue.') {
  const response = err?.response?.data
  const detail =
    (Array.isArray(response?.detail) && response.detail.length && response.detail[0]) ||
    response?.message ||
    response?.error

  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim()
  }

  if (typeof err.message === 'string' && err.message.trim()) {
    return err.message.trim()
  }

  return fallback
}
</script>
