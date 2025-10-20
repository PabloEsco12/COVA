<template>
  <div class="devices-page p-4">
    <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4">
      <div>
        <h2 class="mb-1">
          <i class="bi bi-phone"></i>
          Appareils connectes
        </h2>
        <p class="text-muted mb-0 small">
          Controle les navigateurs et applications autorises a utiliser ton compte COVA.
        </p>
      </div>
      <div class="d-flex gap-2">
        <button class="btn btn-outline-primary" type="button" @click="renameCurrentDevice" :disabled="registering">
          <i class="bi bi-pencil-square me-2"></i>
          Renommer cet appareil
        </button>
        <button class="btn btn-outline-secondary" type="button" @click="manualSync" :disabled="registering">
          <span v-if="registering" class="spinner-border spinner-border-sm me-2" role="status"></span>
          <span v-else><i class="bi bi-arrow-repeat me-2"></i>Resynchroniser</span>
        </button>
      </div>
    </div>

    <div v-if="error" class="alert alert-danger d-flex align-items-center gap-2" role="alert">
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{{ error }}</span>
    </div>
    <div v-if="success" class="alert alert-success d-flex align-items-center gap-2" role="status">
      <i class="bi bi-check-circle-fill"></i>
      <span>{{ success }}</span>
    </div>

    <div v-if="loading" class="py-5">
      <Spinner />
      <p class="text-center text-muted mt-3">Chargement des appareils...</p>
    </div>

    <div v-else>
      <div v-if="deviceCards.length === 0" class="card empty-state border-0 shadow-sm">
        <div class="card-body text-center py-5">
          <div class="empty-icon mb-3">
            <i class="bi bi-shield-lock"></i>
          </div>
          <h5 class="mb-2">Aucun appareil enregistre</h5>
          <p class="text-muted mb-4">
            Des que tu utilises COVA depuis un nouvel appareil securise, il apparaitra ici. Tu peux aussi enregistrer manuellement cet appareil.
          </p>
          <button class="btn btn-primary" type="button" @click="manualSync" :disabled="registering">
            <span v-if="registering" class="spinner-border spinner-border-sm me-2" role="status"></span>
            <span v-else>Enregistrer cet appareil</span>
          </button>
        </div>
      </div>

      <div v-else class="row g-4">
        <div v-for="device in deviceCards" :key="device.id" class="col-xl-4 col-lg-6">
          <div :class="['card h-100 device-card', device.isCurrent ? 'card-current' : '']">
            <div class="card-body d-flex flex-column">
              <div class="d-flex align-items-start gap-3">
                <div :class="['device-avatar', device.iconClass]">
                  <i :class="device.icon"></i>
                </div>
                <div class="flex-grow-1">
                  <div class="d-flex align-items-start justify-content-between">
                    <div>
                      <h5 class="card-title mb-1">{{ device.label }}</h5>
                      <p class="card-subtitle text-muted small mb-2" v-if="device.subtitle">{{ device.subtitle }}</p>
                    </div>
                    <span v-if="device.isCurrent" class="badge rounded-pill text-bg-primary fw-semibold">Cet appareil</span>
                  </div>
                  <ul class="list-unstyled small mb-0 text-muted device-meta">
                    <li>
                      <i class="bi bi-clock me-2"></i>
                      Enregistre le {{ device.createdAt }}
                    </li>
                    <li v-if="device.timezone">
                      <i class="bi bi-globe me-2"></i>
                      Fuseau {{ device.timezone }}
                    </li>
                    <li v-if="device.language">
                      <i class="bi bi-translate me-2"></i>
                      Langue {{ device.language }}
                    </li>
                    <li v-if="device.screen">
                      <i class="bi bi-aspect-ratio me-2"></i>
                      Ecran {{ device.screen }}
                    </li>
                    <li v-if="device.lastSync">
                      <i class="bi bi-arrow-repeat me-2"></i>
                      Synchro {{ device.lastSync }}
                    </li>
                  </ul>
                </div>
              </div>

              <div class="mt-auto pt-3 d-flex flex-column gap-2">
                <div class="device-id text-muted small">
                  ID: {{ device.id }}
                </div>
                <div class="d-flex gap-2">
                  <button
                    class="btn btn-outline-danger flex-grow-1"
                    type="button"
                    @click="revokeDevice(device.id)"
                    :disabled="device.isCurrent || revoking === device.id"
                  >
                    <span v-if="revoking === device.id" class="spinner-border spinner-border-sm me-2"></span>
                    {{ device.isCurrent ? 'Session active' : 'Deconnecter' }}
                  </button>
                  <button
                    class="btn btn-outline-secondary"
                    type="button"
                    @click="showDeviceDetails(device)"
                  >
                    <i class="bi bi-info-circle"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <div v-if="detailsModal" class="modal-backdrop"></div>
    <div v-if="detailsModal" class="device-modal">
      <div class="device-modal-dialog">
        <div class="device-modal-header">
          <h5 class="mb-0">Details de l appareil</h5>
          <button type="button" class="btn-close" @click="detailsModal = null"></button>
        </div>
        <div class="device-modal-body">
          <p class="mb-2"><strong>{{ detailsModal.label }}</strong></p>
          <ul class="list-unstyled small mb-0">
            <li v-if="detailsModal.subtitle"><strong>Profil</strong>: {{ detailsModal.subtitle }}</li>
            <li><strong>Identifiant</strong>: {{ detailsModal.id }}</li>
            <li v-if="detailsModal.timezone"><strong>Fuseau</strong>: {{ detailsModal.timezone }}</li>
            <li v-if="detailsModal.language"><strong>Langue</strong>: {{ detailsModal.language }}</li>
            <li v-if="detailsModal.screen"><strong>Ecran</strong>: {{ detailsModal.screen }}</li>
            <li v-if="detailsModal.metadata?.userAgent"><strong>User agent</strong>: {{ detailsModal.metadata.userAgent }}</li>
            <li v-if="detailsModal.metadata?.raw"><strong>Token</strong>: {{ detailsModal.metadata.raw }}</li>
          </ul>
        </div>
        <div class="device-modal-footer">
          <button class="btn btn-secondary" type="button" @click="detailsModal = null">Fermer</button>
          <button
            v-if="!detailsModal.isCurrent"
            class="btn btn-outline-danger"
            type="button"
            @click="handleModalRevoke"
            :disabled="revoking === detailsModal.id"
          >
            <span v-if="revoking === detailsModal.id" class="spinner-border spinner-border-sm me-2"></span>
            Deconnecter
          </button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import Spinner from './Spinner.vue'
import { api } from '../utils/api'

const devices = ref([])
const loading = ref(true)
const error = ref('')
const success = ref('')
const registering = ref(false)
const revoking = ref('')
const detailsModal = ref(null)

const deviceStorageKey = 'cova_device_id'
const deviceLabelKey = 'cova_device_label'
const localDeviceId = ref('')
let successTimer = null
let autoRegistrationTried = false

const currentDevicePresent = computed(() =>
  devices.value.some((d) => d.id === localDeviceId.value)
)

const deviceCards = computed(() => {
  return devices.value
    .map((raw) => {
      const metadata = decodeMetadata(raw.push_token)
      const ua = metadata.userAgent || metadata.ua || ''
      const browser = metadata.browser || detectBrowser(ua)
      const os = metadata.os || detectOs(ua)
      const deviceType =
        metadata.deviceType || detectDeviceType(ua) || convertPlatformToType(raw.platform)
      const label = trimLabel(metadata.label || detectDefaultLabel({ browser, os }))
      const subtitle = buildSubtitle(browser, os)
      const screen = metadata.screen || metadata.screenSize || ''
      const timezone = metadata.timezone || metadata.tz || ''
      const language = metadata.language || metadata.lang || ''
      const lastSync = metadata.syncedAt ? formatDate(metadata.syncedAt) : ''
      const iconData = pickIcon(deviceType)

      return {
        id: raw.id,
        rawCreatedAt: raw.created_at,
        createdAt: formatDate(raw.created_at),
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
    })
    .sort((a, b) => {
      if (a.isCurrent && !b.isCurrent) return -1
      if (!a.isCurrent && b.isCurrent) return 1

      const dateA = new Date(a.rawCreatedAt)
      const dateB = new Date(b.rawCreatedAt)
      if (Number.isNaN(dateA.getTime()) || Number.isNaN(dateB.getTime())) return 0
      return dateB.getTime() - dateA.getTime()
    })
})

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
  await loadDevices()
  if (!autoRegistrationTried && localDeviceId.value && !currentDevicePresent.value) {
    autoRegistrationTried = true
    try {
      await syncCurrentDevice({ silent: true })
      await loadDevices()
    } catch {
      // ignore auto sync failure
    }
  }
}

async function loadDevices() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/me/devices')
    devices.value = Array.isArray(data?.devices) ? data.devices : []
  } catch (e) {
    error.value = extractError(e, 'Impossible de recuperer les appareils pour le moment.')
  } finally {
    loading.value = false
  }
}

async function manualSync() {
  try {
    await syncCurrentDevice({ silent: false })
    await loadDevices()
  } catch {
    // syncCurrentDevice already surfaced the error
  }
}

async function syncCurrentDevice({ silent } = { silent: false }) {
  if (!localDeviceId.value) {
    localDeviceId.value = ensureLocalDeviceId()
  }
  if (!localDeviceId.value) {
    if (!silent) {
      error.value = 'Impossible de generer un identifiant pour cet appareil.'
    }
    return
  }

  const meta = buildMetadata()
  const payload = encodeMetadata({
    ...meta,
    deviceId: localDeviceId.value,
  })
  if (!payload) {
    if (!silent) {
      error.value = 'Impossible de preparer les informations de cet appareil.'
    }
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
    if (!silent) {
      setSuccessMessage('Appareil synchronise.')
    }
  } catch (e) {
    if (!silent) {
      error.value = extractError(e, "Impossible d'enregistrer cet appareil pour le moment.")
    }
    throw e
  } finally {
    if (!silent) {
      registering.value = false
    }
  }
}

async function revokeDevice(id) {
  if (!id || revoking.value) return
  error.value = ''
  revoking.value = id
  try {
    await api.delete(`/me/devices/${id}`)
    setSuccessMessage('Appareil deconnecte.')
    if (detailsModal.value && detailsModal.value.id === id) {
      detailsModal.value = null
    }
    await loadDevices()
  } catch (e) {
    error.value = extractError(e, 'Impossible de deconnecter cet appareil.')
  } finally {
    revoking.value = ''
  }
}

function showDeviceDetails(device) {
  detailsModal.value = device
}

async function handleModalRevoke() {
  if (!detailsModal.value) return
  await revokeDevice(detailsModal.value.id)
  if (!error.value) {
    detailsModal.value = null
  }
}

async function renameCurrentDevice() {
  const current = deviceCards.value.find((d) => d.isCurrent)
  const stored = safeGetLocal(deviceLabelKey)
  const currentLabel = current?.metadata?.label || stored || detectDefaultLabel({})
  const next =
    typeof window !== 'undefined'
      ? window.prompt('Choisis un nom pour cet appareil', currentLabel || '')
      : ''
  if (next === null || typeof next === 'undefined') return
  const trimmed = next.trim().slice(0, 60)
  if (!trimmed) return
  try {
    localStorage.setItem(deviceLabelKey, trimmed)
  } catch {
    // storage may be unavailable
  }
  await manualSync()
}

function ensureLocalDeviceId() {
  if (typeof window === 'undefined') return ''
  try {
    let id = localStorage.getItem(deviceStorageKey)
    if (!id) {
      if (window.crypto && typeof window.crypto.randomUUID === 'function') {
        id = window.crypto.randomUUID()
      } else {
        id = `web-${Math.random().toString(36).slice(2, 10)}-${Date.now().toString(36)}`
      }
      localStorage.setItem(deviceStorageKey, id)
    }
    return id
  } catch {
    return ''
  }
}

function buildMetadata() {
  const nav = typeof window !== 'undefined' ? window.navigator : undefined
  const ua = nav?.userAgent || ''
  const browser = detectBrowser(ua)
  const os = detectOs(ua)
  const deviceType = detectDeviceType(ua)
  const timezone = (() => {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone || ''
    } catch {
      return ''
    }
  })()
  const language = nav?.language || ''
  const screenSize =
    typeof window !== 'undefined' && window.screen
      ? `${window.screen.width}x${window.screen.height}`
      : ''
  const storedLabel = safeGetLocal(deviceLabelKey)
  const label = trimLabel(storedLabel || detectDefaultLabel({ browser, os }))
  return {
    label,
    browser,
    os,
    deviceType,
    timezone,
    language,
    screen: screenSize,
    userAgent: ua,
    syncedAt: new Date().toISOString(),
  }
}

function encodeMetadata(meta) {
  try {
    const json = JSON.stringify(meta)
    if (typeof TextEncoder !== 'undefined') {
      const encoded = new TextEncoder().encode(json)
      let binary = ''
      encoded.forEach((byte) => {
        binary += String.fromCharCode(byte)
      })
      return btoa(binary)
    }
    return btoa(unescape(encodeURIComponent(json)))
  } catch {
    return ''
  }
}

function decodeMetadata(raw) {
  if (!raw) return {}
  try {
    const binary = atob(raw)
    const bytes = Uint8Array.from(binary, (ch) => ch.charCodeAt(0))
    let text = ''
    if (typeof TextDecoder !== 'undefined') {
      text = new TextDecoder().decode(bytes)
    } else {
      text = Array.from(bytes)
        .map((byte) => String.fromCharCode(byte))
        .join('')
    }
    const data = JSON.parse(text)
    return typeof data === 'object' && data ? data : {}
  } catch {
    try {
      const data = JSON.parse(raw)
      return typeof data === 'object' && data ? data : { raw }
    } catch {
      return { raw }
    }
  }
}

function detectBrowser(ua) {
  if (!ua) return ''
  if (/MSIE|Trident/.test(ua)) return 'Internet Explorer'
  const matchers = [
    { name: 'Edge', regex: /Edg\/([\d.]+)/ },
    { name: 'Chrome', regex: /Chrome\/([\d.]+)/ },
    { name: 'Firefox', regex: /Firefox\/([\d.]+)/ },
    { name: 'Safari', regex: /Version\/([\d.]+).*Safari/ },
    { name: 'Opera', regex: /OPR\/([\d.]+)/ },
  ]
  for (const entry of matchers) {
    const found = ua.match(entry.regex)
    if (found) {
      return `${entry.name} ${found[1].split('.')[0]}`
    }
  }
  return ''
}

function detectOs(ua) {
  if (!ua) return ''
  if (/Windows NT 10/.test(ua) || /Windows NT 11/.test(ua)) return 'Windows 10/11'
  if (/Windows NT 6\.3/.test(ua)) return 'Windows 8.1'
  if (/Windows NT 6\.1/.test(ua)) return 'Windows 7'
  if (/Mac OS X 10[._]\d+/.test(ua)) return 'macOS'
  if (/Android/.test(ua)) return 'Android'
  if (/(iPhone|iPad|iPod)/.test(ua)) return 'iOS'
  if (/Linux/.test(ua)) return 'Linux'
  return ''
}

function detectDeviceType(ua) {
  if (!ua) return ''
  if (/Tablet|iPad/.test(ua)) return 'tablet'
  if (/Mobi|Android/.test(ua)) return 'mobile'
  return 'desktop'
}

function convertPlatformToType(platform) {
  if (!platform) return ''
  const lower = platform.toLowerCase()
  if (lower.includes('mobile')) return 'mobile'
  if (lower.includes('tablet')) return 'tablet'
  return 'desktop'
}

function pickIcon(type) {
  if (type === 'mobile') {
    return { icon: 'bi bi-phone', iconClass: 'is-mobile' }
  }
  if (type === 'tablet') {
    return { icon: 'bi bi-tablet', iconClass: 'is-tablet' }
  }
  return { icon: 'bi bi-laptop', iconClass: 'is-desktop' }
}

function detectDefaultLabel({ browser = '', os = '' }) {
  if (browser && os) return `${browser} on ${os}`
  if (browser) return browser
  if (os) return os
  return 'Web device'
}

function buildSubtitle(browser, os) {
  const parts = []
  if (browser) parts.push(browser)
  if (os) parts.push(os)
  return parts.join(' - ')
}

function trimLabel(label) {
  if (!label) return ''
  return label.length > 60 ? `${label.slice(0, 57)}...` : label
}

function safeGetLocal(key) {
  if (typeof window === 'undefined') return ''
  try {
    return localStorage.getItem(key) || ''
  } catch {
    return ''
  }
}

function mapDeviceTypeToPlatform(type) {
  if (type === 'mobile') return 'Mobile'
  if (type === 'tablet') return 'Tablet'
  return 'Web'
}

function formatDate(value) {
  if (!value) return 'Inconnu'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return 'Inconnu'
  try {
    return new Intl.DateTimeFormat('fr-FR', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(date)
  } catch {
    return date.toLocaleString()
  }
}

function extractError(err, fallback) {
  const message = err?.response?.data?.error || err?.message
  return message || fallback
}

function setSuccessMessage(message) {
  success.value = message
  error.value = ''
  if (successTimer) {
    clearTimeout(successTimer)
  }
  successTimer = setTimeout(() => {
    success.value = ''
    successTimer = null
  }, 4000)
}
</script>

<style scoped src="../styles/components/Devices.css"></style>
