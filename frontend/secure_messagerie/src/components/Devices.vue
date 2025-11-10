<template>
  <div class="devices-page">
    <header class="page-header">
      <div>
        <h2 class="title">
          <i class="bi bi-phone me-2"></i>
          Appareils connectes
        </h2>
        <p class="subtitle">
          Surveillez les terminaux autorises et deconnectez les sessions douteuses en un clic.
        </p>
      </div>
      <div class="header-actions">
        <button
          class="btn btn-outline-danger"
          type="button"
          @click="logoutEverywhere"
          :disabled="logoutBusy || registering || loading"
        >
          <span v-if="logoutBusy" class="spinner-border spinner-border-sm me-2"></span>
          <span v-else class="me-2"><i class="bi bi-shield-x"></i></span>
          Deconnecter tous les appareils
        </button>
        <button class="btn btn-outline-secondary" type="button" @click="manualSync" :disabled="registering">
          <span v-if="registering" class="spinner-border spinner-border-sm me-2"></span>
          <span v-else class="me-2"><i class="bi bi-arrow-repeat"></i></span>
          Synchroniser
        </button>
        <button class="btn btn-primary" type="button" @click="openRenameModal" :disabled="registering">
          <i class="bi bi-pencil-square me-2"></i>
          Nommer cet appareil
        </button>
      </div>
    </header>

    <section v-if="deviceCards.length" class="security-summary card">
      <div class="summary-grid">
        <div class="summary-item">
          <h6 class="label">Appareils enregistres</h6>
          <p class="value">{{ summary.total }}</p>
          <span class="hint">{{ summary.currentLabel }}</span>
        </div>
        <div class="summary-item">
          <h6 class="label">Activite recente</h6>
          <p class="value">{{ summary.lastSeenRelative || 'Jamais' }}</p>
          <span class="hint" v-if="summary.lastSeenAt">Dernier acces {{ summary.lastSeenAt }}</span>
        </div>
        <div class="summary-item">
          <h6 class="label">Surveillance</h6>
          <p class="value" :class="{ 'text-warning': summary.risky > 0 }">{{ summary.risky }}</p>
          <span class="hint">
            {{ summary.risky > 0 ? 'Appareil(s) a verifier' : 'Aucun signal faible' }}
          </span>
        </div>
      </div>
    </section>

    <div v-if="error" class="alert alert-danger d-flex align-items-center gap-2">
      <i class="bi bi-exclamation-triangle-fill"></i>
      <span>{{ error }}</span>
    </div>
    <div v-if="success" class="alert alert-success d-flex align-items-center gap-2">
      <i class="bi bi-check-circle-fill"></i>
      <span>{{ success }}</span>
    </div>

    <div v-if="loading" class="loader-stack">
      <Spinner></Spinner>
      <p class="text-muted mt-3">Recuperation de vos appareils securises...</p>
    </div>

    <div v-else>
      <section v-if="!deviceCards.length" class="empty-state card">
        <div class="card-body text-center">
          <div class="empty-icon mb-3"><i class="bi bi-shield-lock"></i></div>
          <h5 class="mb-2">Aucun appareil enregistre</h5>
          <p class="text-muted mb-4">
            Connectez-vous depuis un navigateur fiable ou synchronisez cet appareil pour l'ajouter.
          </p>
          <button class="btn btn-primary" type="button" @click="manualSync" :disabled="registering">
            <span v-if="registering" class="spinner-border spinner-border-sm me-2"></span>
            <span v-else>Enregistrer cet appareil</span>
          </button>
        </div>
      </section>

      <section v-else class="device-grid">
        <article
          v-for="device in deviceCards"
          :key="device.id"
          class="device-card card"
          :class="[{ 'device-card--current': device.isCurrent }, 'device-card--' + device.trustVariant]"
        >
          <div class="card-body d-flex flex-column gap-3">
            <div class="d-flex align-items-start gap-3">
              <div :class="['device-avatar', device.iconClass]">
                <i :class="device.icon"></i>
              </div>
              <div class="flex-grow-1">
                <div class="device-heading">
                  <div>
                    <h5 class="mb-1">{{ device.label }}</h5>
                    <p v-if="device.subtitle" class="text-muted small mb-2">{{ device.subtitle }}</p>
                  </div>
                  <div class="badge-stack">
                    <span v-if="device.isCurrent" class="badge text-bg-primary">Cet appareil</span>
                    <span class="trust-chip" :class="'trust-chip--' + device.trustVariant">
                      <i :class="device.trustIcon" class="me-1"></i>
                      {{ device.trustLabel }}
                    </span>
                  </div>
                </div>

                <ul class="device-meta list-unstyled small mb-0">
                  <li>
                    <i class="bi bi-clock me-2"></i>
                    Inscrit le {{ device.createdAt }}
                  </li>
                  <li v-if="device.lastSeenAt">
                    <i class="bi bi-activity me-2"></i>
                    Vu {{ device.lastSeenRelative }}
                    <span class="text-muted">({{ device.lastSeenAt }})</span>
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
                    Derniere synchro {{ device.lastSync }}
                  </li>
                </ul>
              </div>
            </div>

            <div class="device-actions d-flex flex-wrap gap-2">
              <button class="btn btn-outline-secondary btn-sm" type="button" @click="openDetails(device)">
                <i class="bi bi-info-circle me-1"></i>
                Details
              </button>
              <button
                class="btn btn-outline-danger btn-sm"
                type="button"
                :disabled="device.isCurrent || revoking === device.id"
                @click="openDeleteModal(device)"
              >
                <span v-if="revoking === device.id" class="spinner-border spinner-border-sm me-1"></span>
                Deconnecter
              </button>
            </div>

            <div class="device-id text-muted small">
              ID client : <span>{{ device.id }}</span>
            </div>
          </div>
        </article>
      </section>
    </div>

    <transition name="fade">
      <div v-if="detailsModal" class="modal-backdrop"></div>
    </transition>
    <transition name="scale">
      <div v-if="detailsModal" class="modal-wrapper" @click.self="detailsModal = null">
        <div class="modal-card">
          <header class="modal-header">
            <div>
              <h5 class="mb-0">Details de l'appareil</h5>
              <small class="text-muted">Verifiez que cet appareil vous appartient.</small>
            </div>
            <button class="btn btn-sm btn-outline-secondary" type="button" @click="detailsModal = null">
              <i class="bi bi-x-lg"></i>
            </button>
          </header>
          <div class="modal-body">
            <div class="modal-device-heading">
              <div :class="['device-avatar', detailsModal.iconClass]">
                <i :class="detailsModal.icon"></i>
              </div>
              <div>
                <h6 class="mb-1">{{ detailsModal.label }}</h6>
                <p v-if="detailsModal.subtitle" class="text-muted small mb-0">{{ detailsModal.subtitle }}</p>
              </div>
            </div>
            <div class="modal-info-grid">
              <div>
                <h6>Informations generales</h6>
                <ul class="list-unstyled small mb-0">
                  <li><strong>ID client</strong> : {{ detailsModal.id }}</li>
                  <li v-if="detailsModal.timezone"><strong>Fuseau</strong> : {{ detailsModal.timezone }}</li>
                  <li v-if="detailsModal.language"><strong>Langue</strong> : {{ detailsModal.language }}</li>
                  <li v-if="detailsModal.screen"><strong>Ecran</strong> : {{ detailsModal.screen }}</li>
                  <li><strong>Inscrit</strong> : {{ detailsModal.createdAt }}</li>
                  <li v-if="detailsModal.lastSeenAt">
                    <strong>Dernier acces</strong> : {{ detailsModal.lastSeenAt }} ({{ detailsModal.lastSeenRelative }})
                  </li>
                </ul>
              </div>
              <div>
                <h6>Contexte navigateur</h6>
                <p class="small text-muted mb-1">User agent transmis :</p>
                <code class="payload-block">{{ detailsModal.metadata.userAgent || 'Non communique' }}</code>
                <p v-if="detailsModal.metadata.raw" class="small text-muted mt-2">
                  Payload brut : <code>{{ detailsModal.metadata.raw }}</code>
                </p>
              </div>
            </div>
          </div>
          <footer class="modal-footer">
            <button class="btn btn-outline-secondary" type="button" @click="detailsModal = null">Fermer</button>
            <button
              v-if="!detailsModal.isCurrent"
              class="btn btn-outline-danger"
              type="button"
              :disabled="revoking === detailsModal.id"
              @click="confirmDelete(detailsModal)"
            >
              <span v-if="revoking === detailsModal.id" class="spinner-border spinner-border-sm me-1"></span>
              Deconnecter
            </button>
          </footer>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showRenameModal" class="modal-backdrop"></div>
    </transition>
    <transition name="scale">
      <div v-if="showRenameModal" class="modal-wrapper" @click.self="closeRenameModal">
        <div class="modal-card">
          <header class="modal-header">
            <div>
              <h5 class="mb-0">Nommer cet appareil</h5>
              <small class="text-muted">Cette etiquette est synchronisee et vous aide a identifier le terminal.</small>
            </div>
            <button class="btn btn-sm btn-outline-secondary" type="button" @click="closeRenameModal">
              <i class="bi bi-x-lg"></i>
            </button>
          </header>
          <div class="modal-body">
            <label class="form-label small text-muted">Nom personnalise</label>
            <input
              ref="renameInput"
              v-model.trim="renameValue"
              type="text"
              maxlength="60"
              class="form-control"
              placeholder="Laptop bureau"
            />
            <p class="text-muted small mt-2 mb-0">
              Le nom est sauvegarde localement puis transmis lors des prochaines synchronisations.
            </p>
            <p v-if="renameError" class="text-danger small mt-2 mb-0">{{ renameError }}</p>
          </div>
          <footer class="modal-footer">
            <button class="btn btn-outline-secondary" type="button" @click="closeRenameModal" :disabled="renameBusy">
              Annuler
            </button>
            <button class="btn btn-primary" type="button" @click="confirmRename" :disabled="renameBusy">
              <span v-if="renameBusy" class="spinner-border spinner-border-sm me-1"></span>
              Enregistrer
            </button>
          </footer>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showDeleteModal" class="modal-backdrop"></div>
    </transition>
    <transition name="scale">
      <div v-if="showDeleteModal" class="modal-wrapper" @click.self="closeDeleteModal">
        <div class="modal-card danger-card">
          <header class="modal-header">
            <div>
              <h5 class="mb-0 text-danger">Deconnecter l'appareil ?</h5>
              <small class="text-muted">La session sera invalidee et devra etre reautorisee avec MFA.</small>
            </div>
            <button class="btn btn-sm btn-outline-secondary" type="button" @click="closeDeleteModal" :disabled="deleteBusy">
              <i class="bi bi-x-lg"></i>
            </button>
          </header>
          <div class="modal-body">
            <div class="delete-preview" v-if="deleteTarget">
              <div :class="['device-avatar', deleteTarget.iconClass]">
                <i :class="deleteTarget.icon"></i>
              </div>
              <div>
                <h6 class="mb-1">{{ deleteTarget.label }}</h6>
                <p class="text-muted small mb-0">{{ deleteTarget.subtitle || deleteTarget.id }}</p>
              </div>
            </div>
            <p class="text-muted small mt-3 mb-0">
              Le terminal devra se reconnecter avec mot de passe et code MFA. Les messages restent conserves.
            </p>
            <div v-if="deleteError" class="alert alert-danger py-2 mt-3">{{ deleteError }}</div>
          </div>
          <footer class="modal-footer">
            <button class="btn btn-outline-secondary" type="button" @click="closeDeleteModal" :disabled="deleteBusy">
              Annuler
            </button>
            <button class="btn btn-danger" type="button" @click="confirmDelete()" :disabled="deleteBusy">
              <span v-if="deleteBusy" class="spinner-border spinner-border-sm me-1"></span>
              Deconnecter
            </button>
          </footer>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import Spinner from './Spinner.vue'
import { api } from '../utils/api'

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
const renameError = ref('')
const renameBusy = ref(false)
const renameInput = ref(null)

const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const deleteBusy = ref(false)
const deleteError = ref('')

const deviceStorageKey = 'cova_device_id'
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
  await loadDevices()
  if (!autoRegistrationTried && localDeviceId.value && !currentDevicePresent.value) {
    autoRegistrationTried = true
    try {
      await syncCurrentDevice({ silent: true })
      await loadDevices()
    } catch {
      // ignore
    }
  }
}

async function loadDevices() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await api.get('/me/devices')
    devices.value = Array.isArray(data?.devices) ? data.devices : []
  } catch (err) {
    error.value = extractError(err, 'Impossible de recuperer vos appareils pour le moment.')
  } finally {
    loading.value = false
  }
}

async function manualSync() {
  try {
    await syncCurrentDevice({ silent: false })
    await loadDevices()
  } catch {
    // erreur deja affichee
  }
}

async function syncCurrentDevice({ silent } = { silent: false }) {
  if (!localDeviceId.value) {
    localDeviceId.value = ensureLocalDeviceId()
  }
  if (!localDeviceId.value) {
    if (!silent) error.value = "Impossible de generer un identifiant pour cet appareil."
    return
  }

  const meta = buildMetadata()
  const payload = encodeMetadata({ ...meta, deviceId: localDeviceId.value })
  if (!payload) {
    if (!silent) error.value = "Impossible de preparer l'empreinte de cet appareil."
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
    if (!silent) setSuccessMessage('Appareil synchronise.')
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
  const current = deviceCards.value.find((device) => device.isCurrent)
  const stored = safeGetLocal(deviceLabelKey)
  renameValue.value = current?.metadata.label || stored || detectDefaultLabel({})
  renameError.value = ''
  showRenameModal.value = true
  nextTick(() => renameInput.value?.focus())
}

function closeRenameModal() {
  if (renameBusy.value) return
  showRenameModal.value = false
}

async function confirmRename() {
  renameError.value = ''
  const nextLabel = (renameValue.value || '').trim().slice(0, 60)
  if (!nextLabel) {
    renameError.value = 'Veuillez saisir un nom comprehensible.'
    return
  }
  renameBusy.value = true
  try {
    localStorage.setItem(deviceLabelKey, nextLabel)
    showRenameModal.value = false
    await manualSync()
    setSuccessMessage("Nom de l'appareil mis a jour.")
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
  let target = deviceOverride
  if (target && !target.id && target.target) {
    target = null
  }
  if (!target) {
    target = deleteTarget.value
  }
  if (!target || deleteBusy.value) return
  if (!target.id) {
    deleteError.value = 'Identifiant de l’appareil indisponible.'
    return
  }
  deleteBusy.value = true
  deleteError.value = ''
  revoking.value = target.id
  try {
    await api.delete(`/me/devices/${target.id}`)
    setSuccessMessage('Appareil deconnecte.')
    showDeleteModal.value = false
    detailsModal.value = null
    await loadDevices()
  } catch (err) {
    const message = extractError(err, 'Impossible de deconnecter cet appareil.')
    deleteError.value = message
    error.value = message
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
    setSuccessMessage('Toutes les sessions sont invalidees.')
    await loadDevices()
  } catch (err) {
    error.value = extractError(err, 'Impossible de deconnecter les autres appareils.')
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
  if (!list.length) {
    return {
      total: 0,
      risky: 0,
      lastSeenAt: '',
      lastSeenRelative: '',
      currentLabel: 'Aucun appareil actif',
    }
  }

  const total = list.length
  const risky = list.filter((device) => ['watch', 'alert'].includes(device.trustVariant)).length
  const current = list.find((device) => device.isCurrent)
  const lastSeen = [...list]
    .filter((device) => device.lastSeenAt)
    .sort((a, b) => new Date(b.lastSeenAt).getTime() - new Date(a.lastSeenAt).getTime())[0]

  return {
    total,
    risky,
    lastSeenAt: lastSeen?.lastSeenAt || '',
    lastSeenRelative: lastSeen?.lastSeenRelative || '',
    currentLabel: current ? `Cet appareil · ${current.label}` : 'Aucun appareil local detecte',
  }
}

function detectDefaultLabel({ browser, os } = {}) {
  const parts = []
  if (browser) parts.push(browser)
  if (os) parts.push(os)
  return parts.length ? parts.join(' · ') : 'Appareil sécurisé'
}

function trimLabel(value) {
  if (!value) return ''
  return value.toString().replace(/\s+/g, ' ').trim().slice(0, 60)
}

function buildSubtitle(browser, os) {
  if (browser && os) return `${browser} • ${os}`
  return browser || os || ''
}

function ensureLocalDeviceId() {
  const existing = safeGetLocal(deviceStorageKey)
  if (existing) return existing
  const next = generateDeviceId()
  try {
    localStorage.setItem(deviceStorageKey, next)
  } catch {}
  return next
}

function generateDeviceId() {
  try {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID()
    }
  } catch {}
  return `dev_${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`
}

function safeGetLocal(key) {
  try {
    return localStorage.getItem(key) || ''
  } catch {
    return ''
  }
}

function buildMetadata() {
  const now = new Date().toISOString()
  const ua = typeof navigator !== 'undefined' ? navigator.userAgent : ''
  const browser = detectBrowser(ua)
  const os = detectOs(ua)
  const deviceType = detectDeviceType(ua)

  const metadata = {
    userAgent: ua,
    browser,
    os,
    deviceType,
    label: trimLabel(safeGetLocal(deviceLabelKey) || detectDefaultLabel({ browser, os })),
    timezone:
      typeof Intl !== 'undefined' && Intl.DateTimeFormat
        ? Intl.DateTimeFormat().resolvedOptions().timeZone || ''
        : '',
    language:
      typeof navigator !== 'undefined'
        ? navigator.language || (Array.isArray(navigator.languages) ? navigator.languages[0] : '') || ''
        : '',
    screen:
      typeof window !== 'undefined' && window.screen
        ? `${window.screen.width || 0}x${window.screen.height || 0}`
        : '',
    syncedAt: now,
  }

  return metadata
}

function mapTrust(score) {
  if (score >= 80) {
    return { variant: 'trusted', label: 'Fiable', icon: 'bi bi-shield-check' }
  }
  if (score >= 55) {
    return { variant: 'standard', label: 'Approuvé', icon: 'bi bi-shield' }
  }
  if (score >= 35) {
    return { variant: 'watch', label: 'À surveiller', icon: 'bi bi-exclamation-triangle' }
  }
  return { variant: 'alert', label: 'Risque élevé', icon: 'bi bi-shield-exclamation' }
}

function pickIcon(type) {
  switch (type) {
    case 'mobile':
      return { icon: 'bi bi-phone', iconClass: 'device-avatar--mobile' }
    case 'tablet':
      return { icon: 'bi bi-tablet', iconClass: 'device-avatar--tablet' }
    case 'tv':
      return { icon: 'bi bi-tv', iconClass: 'device-avatar--tv' }
    case 'bot':
      return { icon: 'bi bi-robot', iconClass: 'device-avatar--bot' }
    case 'desktop':
    default:
      return { icon: 'bi bi-pc-display', iconClass: 'device-avatar--desktop' }
  }
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
  const agent = ua.toLowerCase()
  if (!agent) return ''
  if (agent.includes('edg/')) return 'Microsoft Edge'
  if (agent.includes('opr/') || agent.includes('opera')) return 'Opera'
  if (agent.includes('firefox/')) return 'Firefox'
  if (agent.includes('safari/') && !agent.includes('chrome')) return 'Safari'
  if (agent.includes('chrome/')) return 'Chrome'
  if (agent.includes('brave/')) return 'Brave'
  if (agent.includes('electron/')) return 'Electron'
  if (agent.includes('vivaldi')) return 'Vivaldi'
  return ua.split(' ')[0] || 'Navigateur inconnu'
}

function detectOs(ua = '') {
  const agent = ua.toLowerCase()
  if (agent.includes('windows')) return 'Windows'
  if (agent.includes('mac os x') || agent.includes('macintosh')) return 'macOS'
  if (agent.includes('android')) return 'Android'
  if (agent.includes('iphone') || agent.includes('ipad') || agent.includes('ios')) return 'iOS'
  if (agent.includes('linux')) return 'Linux'
  if (agent.includes('cros')) return 'ChromeOS'
  return ''
}

function detectDeviceType(ua = '') {
  if (/bot|crawler|spider|headless|phantom/i.test(ua)) return 'bot'
  if (/tablet|ipad|tab/i.test(ua)) return 'tablet'
  if (/mobile|iphone|android|blackberry|phone/i.test(ua)) return 'mobile'
  if (/tv|smarttv|appletv|hbbtv/i.test(ua)) return 'tv'
  return 'desktop'
}

function convertPlatformToType(platform) {
  if (!platform) return 'desktop'
  const value = platform.toString().toLowerCase()
  if (value.includes('ios') || value.includes('android') || value.includes('mobile')) return 'mobile'
  if (value.includes('tablet')) return 'tablet'
  if (value.includes('tv')) return 'tv'
  if (value.includes('bot')) return 'bot'
  return 'desktop'
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

function formatDate(input) {
  if (!input) return ''
  const date = new Date(input)
  if (Number.isNaN(date.getTime())) return ''
  try {
    return new Intl.DateTimeFormat('fr-FR', {
      dateStyle: 'medium',
      timeStyle: 'short',
    }).format(date)
  } catch {
    return date.toLocaleString()
  }
}

function formatRelative(input) {
  if (!input) return ''
  const date = new Date(input)
  if (Number.isNaN(date.getTime())) return ''
  const diffSeconds = Math.round((date.getTime() - Date.now()) / 1000)
  const absSeconds = Math.abs(diffSeconds)

  let unit = 'second'
  let value = diffSeconds

  if (absSeconds >= 31557600) {
    unit = 'year'
    value = Math.round(diffSeconds / 31557600)
  } else if (absSeconds >= 2629800) {
    unit = 'month'
    value = Math.round(diffSeconds / 2629800)
  } else if (absSeconds >= 604800) {
    unit = 'week'
    value = Math.round(diffSeconds / 604800)
  } else if (absSeconds >= 86400) {
    unit = 'day'
    value = Math.round(diffSeconds / 86400)
  } else if (absSeconds >= 3600) {
    unit = 'hour'
    value = Math.round(diffSeconds / 3600)
  } else if (absSeconds >= 60) {
    unit = 'minute'
    value = Math.round(diffSeconds / 60)
  }

  if (typeof Intl !== 'undefined' && Intl.RelativeTimeFormat) {
    const formatter = new Intl.RelativeTimeFormat('fr-FR', { numeric: 'auto' })
    return formatter.format(value, unit)
  }

  const prefix = diffSeconds < 0 ? 'il y a ' : 'dans '
  return `${prefix}${Math.abs(value)} ${unit}${Math.abs(value) > 1 ? 's' : ''}`
}

function extractError(err, fallback) {
  if (!err) return fallback
  if (typeof err === 'string') return err

  const response = err.response?.data
  const detail =
    (typeof response?.detail === 'string' && response.detail) ||
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

<style scoped>
.devices-page {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
  padding: 0 0 3rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.page-header .title {
  margin-bottom: 0.25rem;
  font-weight: 600;
  font-size: 1.5rem;
}

.page-header .subtitle {
  color: #6c757d;
  margin: 0;
}

.header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  justify-content: flex-end;
}

.security-summary.card {
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 10px 30px rgba(15, 26, 48, 0.05);
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.summary-item .label {
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #6c757d;
  font-size: 0.75rem;
  margin-bottom: 0.5rem;
}

.summary-item .value {
  font-size: 2rem;
  font-weight: 600;
  margin: 0;
}

.summary-item .hint {
  display: block;
  color: #6c757d;
  font-size: 0.85rem;
}

.loader-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 3rem 0;
}

.empty-state.card {
  border: 1px dashed rgba(13, 110, 253, 0.4);
  border-radius: 1rem;
  background: rgba(13, 110, 253, 0.04);
}

.empty-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 4rem;
  height: 4rem;
  border-radius: 1.5rem;
  color: #0d6efd;
  background: rgba(13, 110, 253, 0.12);
  font-size: 1.75rem;
}

.device-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.device-card.card {
  border-radius: 1.25rem;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 12px 35px rgba(15, 26, 48, 0.08);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
  position: relative;
}

.device-card.card:hover {
  transform: translateY(-4px);
  box-shadow: 0 15px 40px rgba(15, 26, 48, 0.12);
}

.device-card--current {
  border-color: rgba(13, 110, 253, 0.55);
  box-shadow: 0 0 0 2px rgba(13, 110, 253, 0.2);
}

.device-card--trusted::before,
.device-card--standard::before,
.device-card--watch::before,
.device-card--alert::before {
  content: '';
  position: absolute;
  inset: 0;
  border-top-left-radius: 1.25rem;
  border-top-right-radius: 1.25rem;
  height: 4px;
}

.device-card--trusted::before {
  background: linear-gradient(90deg, #198754, #0f5132);
}

.device-card--standard::before {
  background: linear-gradient(90deg, #0d6efd, #0b5ed7);
}

.device-card--watch::before {
  background: linear-gradient(90deg, #ffc107, #b8860b);
}

.device-card--alert::before {
  background: linear-gradient(90deg, #dc3545, #842029);
}

.device-avatar {
  width: 3.25rem;
  height: 3.25rem;
  border-radius: 1.1rem;
  display: grid;
  place-items: center;
  font-size: 1.6rem;
  color: #fff;
}

.device-avatar--desktop {
  background: linear-gradient(135deg, #0d6efd, #6ea8fe);
}

.device-avatar--mobile {
  background: linear-gradient(135deg, #6610f2, #b197fc);
}

.device-avatar--tablet {
  background: linear-gradient(135deg, #20c997, #57d9b1);
}

.device-avatar--tv {
  background: linear-gradient(135deg, #6f42c1, #d0bfff);
}

.device-avatar--bot {
  background: linear-gradient(135deg, #212529, #495057);
}

.device-heading {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.badge-stack {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.trust-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  border-radius: 999px;
  padding: 0.25rem 0.7rem;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.trust-chip--trusted {
  color: #0f5132;
  background: rgba(25, 135, 84, 0.15);
}

.trust-chip--standard {
  color: #084298;
  background: rgba(13, 110, 253, 0.15);
}

.trust-chip--watch {
  color: #997404;
  background: rgba(255, 193, 7, 0.2);
}

.trust-chip--alert {
  color: #842029;
  background: rgba(220, 53, 69, 0.15);
}

.device-meta li {
  margin-bottom: 0.3rem;
  display: flex;
  align-items: center;
  color: #495057;
}

.device-actions .btn {
  min-width: 7rem;
}

.device-id span {
  font-family: 'Fira Code', ui-monospace, SFMono-Regular, 'SFMono-Regular', Menlo, Monaco, Consolas,
    'Liberation Mono', 'Courier New', monospace;
}

.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.45);
  backdrop-filter: blur(3px);
  z-index: 1040;
}

.modal-wrapper {
  position: fixed;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 2rem;
  z-index: 1050;
}

.modal-card {
  width: min(560px, 100%);
  background: #fff;
  border-radius: 1.25rem;
  box-shadow: 0 20px 50px rgba(15, 26, 48, 0.18);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-card.danger-card {
  border-top: 5px solid #dc3545;
}

.modal-header,
.modal-footer {
  padding: 1.25rem 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.modal-body {
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.modal-device-heading {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.modal-info-grid {
  display: grid;
  gap: 1.25rem;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
}

.payload-block {
  display: block;
  background: #f1f3f5;
  border-radius: 0.6rem;
  padding: 0.75rem;
  font-size: 0.85rem;
  overflow-wrap: anywhere;
}

.delete-preview {
  display: flex;
  gap: 0.9rem;
  align-items: center;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.scale-enter-active,
.scale-leave-active {
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.scale-enter-from,
.scale-leave-to {
  transform: scale(0.95);
  opacity: 0;
}

@media (max-width: 992px) {
  .header-actions {
    justify-content: flex-start;
  }

  .device-grid {
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  }

  .modal-wrapper {
    padding: 1.25rem;
    align-items: flex-end;
  }
}

@media (max-width: 576px) {
  .page-header {
    flex-direction: column;
  }

  .header-actions {
    width: 100%;
  }

  .header-actions .btn {
    flex: 1;
  }

  .modal-card {
    width: 100%;
    border-radius: 1rem 1rem 0 0;
  }

  .modal-footer {
    flex-direction: column;
    align-items: stretch;
  }

  .modal-footer .btn {
    width: 100%;
  }
}
</style>
