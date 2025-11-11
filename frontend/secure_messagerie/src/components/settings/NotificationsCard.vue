<template>
  <div class="card p-3 h-100">
    <div class="d-flex justify-content-between align-items-start mb-3">
      <div>
        <h4 class="mb-1">Notifications</h4>
        <p class="text-muted small mb-0">
          Configurez la facon dont SecureChat vous alerte des activites sensibles.
        </p>
      </div>
      <i class="bi bi-bell text-secondary fs-4"></i>
    </div>

    <!-- alertes email -->
    <div class="border rounded-3 p-3 mb-3">
      <div class="d-flex justify-content-between align-items-start">
        <div class="me-3">
          <h5 class="h6 mb-1">Alertes de connexion par e-mail</h5>
          <p class="text-muted small mb-2">
            Recevez un resume securise a chaque authentification reussie.
          </p>
        </div>
        <div class="form-check form-switch">
          <input
            class="form-check-input"
            type="checkbox"
            id="notifLogin"
            v-model="notifLogin"
            @change="saveSecurity"
            :disabled="!preferencesLoaded"
          />
        </div>
      </div>
      <div class="row g-2 mt-2">
        <div class="col-md-6">
          <label for="quietStart" class="form-label small text-muted mb-1">Plage silencieuse (de)</label>
          <input
            id="quietStart"
            type="time"
            class="form-control form-control-sm"
            v-model="emailQuietStart"
            :disabled="loadingEmailPref || !preferencesLoaded"
          />
        </div>
        <div class="col-md-6">
          <label for="quietEnd" class="form-label small text-muted mb-1">Plage silencieuse (a)</label>
          <input
            id="quietEnd"
            type="time"
            class="form-control form-control-sm"
            v-model="emailQuietEnd"
            :disabled="loadingEmailPref || !preferencesLoaded"
          />
        </div>
      </div>
      <div class="d-flex flex-wrap gap-2 mt-3">
        <button
          class="btn btn-outline-primary btn-sm"
          @click="saveEmailPreference"
          :disabled="loadingEmailPref || !preferencesLoaded"
        >
          <span v-if="loadingEmailPref" class="spinner-border spinner-border-sm me-1"></span>
          Enregistrer les preferences e-mail
        </button>
        <button
          class="btn btn-outline-secondary btn-sm"
          @click="sendLoginAlertTest"
          :disabled="sendingTestEmail || !notifLogin || !preferencesLoaded"
        >
          <span v-if="sendingTestEmail" class="spinner-border spinner-border-sm me-1"></span>
          Envoyer un e-mail de test
        </button>
      </div>
      <p class="text-muted small mt-2 mb-0">
        Les alertes critiques restent envoyees immediatement, meme pendant la plage silencieuse.
      </p>
      <div
        v-if="emailPrefMsg"
        :class="['alert mt-3', emailPrefOk ? 'alert-success' : 'alert-danger']"
      >
        {{ emailPrefMsg }}
      </div>
    </div>

    <!-- push navigateur -->
    <div class="border rounded-3 p-3">
      <div class="d-flex justify-content-between align-items-start">
        <div class="me-3">
          <h5 class="h6 mb-1">Notifications navigateur en temps reel</h5>
          <p class="text-muted small mb-2">
            Soyez prevenu instantanement lorsqu'un message confidentiel arrive.
          </p>
        </div>
        <div class="form-check form-switch">
          <input
            class="form-check-input"
            type="checkbox"
            id="notifBrowser"
            :disabled="!browserSupported || syncingPushPref"
            v-model="notifBrowser"
            @change="toggleBrowserNotifications"
          />
        </div>
      </div>
      <div class="d-flex flex-wrap gap-2">
        <button
          class="btn btn-outline-secondary btn-sm"
          @click="testNotification"
          :disabled="!notifBrowser || browserPermission !== 'granted'"
        >
          Tester une notification
        </button>
      </div>
      <div class="mt-2">
        <p v-if="!browserSupported" class="text-muted small mb-0">
          Votre navigateur ne prend pas en charge les notifications push.
        </p>
        <p v-else-if="browserPermission === 'denied'" class="text-danger small mb-0">
          Autorisez SecureChat depuis les parametres de votre navigateur pour recevoir les alertes.
        </p>
        <p v-else-if="browserPermission === 'default'" class="text-muted small mb-0">
          Nous vous demanderons l'autorisation lors de l'activation.
        </p>
        <p v-else class="text-muted small mb-0">Notifications actives sur ce navigateur.</p>
      </div>
      <div
        v-if="browserMsg"
        :class="[
          'alert mt-3',
          browserMsgType === 'success'
            ? 'alert-success'
            : browserMsgType === 'error'
              ? 'alert-danger'
              : browserMsgType === 'warning'
                ? 'alert-warning'
                : 'alert-info',
        ]"
      >
        {{ browserMsg }}
      </div>
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/utils/api'

const notifLogin = ref(false)
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
const notifBrowser = ref(readStoredBrowserPref())

const DEFAULT_TIMEZONE = 'Europe/Brussels'

onMounted(async () => {
  initBrowserDefaults()
  await fetchNotificationPreferences()
})

function readStoredBrowserPref() {
  try {
    return localStorage.getItem('notif_browser') === '1'
  } catch {
    return false
  }
}

function writeStoredBrowserPref(enabled) {
  try {
    localStorage.setItem('notif_browser', enabled ? '1' : '0')
  } catch {}
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

async function fetchNotificationPreferences() {
  try {
    const res = await api.get('/notifications/preferences')
    const prefs = Array.isArray(res.data) ? res.data : []
    const emailPref = prefs.find((item) => item?.channel === 'email')
    if (emailPref && emailPref.quiet_hours) {
      emailQuietStart.value = emailPref.quiet_hours.start || ''
      emailQuietEnd.value = emailPref.quiet_hours.end || ''
    } else {
      emailQuietStart.value = ''
      emailQuietEnd.value = ''
    }
    const pushPref = prefs.find((item) => item?.channel === 'push')
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
    timezone: DEFAULT_TIMEZONE,
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
    await api.put('/notifications/preferences/email', {
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
    const { data } = await api.post('/notifications/test/login-alert')
    emailPrefOk.value = true
    emailPrefMsg.value =
      data?.detail ||
      (data?.skipped
        ? 'Aucune alerte envoyée : plage silencieuse active.'
        : 'E-mail de test programmé. Vérifiez votre messagerie.')
    setTimeout(() => {
      emailPrefMsg.value = ''
    }, 5000)
  } catch (e) {
    const detail = e?.response?.data?.detail || e?.response?.data?.error || ''
    if (
      typeof detail === 'string' &&
      detail.toLowerCase().includes('impossible de programmer le test')
    ) {
      emailPrefOk.value = true
      emailPrefMsg.value =
        'E-mail de test envoyé. Ignorez l’avertissement si vous recevez bien la notification.'
      setTimeout(() => {
        emailPrefMsg.value = ''
      }, 5000)
    } else {
      emailPrefOk.value = false
      emailPrefMsg.value = detail || 'Impossible de programmer un test actuellement.'
    }
  } finally {
    sendingTestEmail.value = false
  }
}

async function saveSecurity() {
  try {
    const res = await api.put('/me/security', { notification_login: notifLogin.value })
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

async function syncPushPreference(enabled) {
  try {
    syncingPushPref.value = true
    await api.put('/notifications/preferences/push', {
      is_enabled: !!enabled,
      quiet_hours: null,
    })
    pushServerAllowed.value = !!enabled
    writeStoredBrowserPref(!!enabled)
  } catch (e) {
    // silencieux
  } finally {
    syncingPushPref.value = false
    refreshBrowserToggle()
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
        browserMsg.value =
          permission === 'denied'
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
    browserMsg.value =
      'Activez les notifications et autorisez-les dans votre navigateur pour lancer un test.'
    return
  }
  try {
    const n = new Notification('COVA Messagerie', {
      body: 'Notification test : vous recevrez les nouveaux messages en temps reel.',
    })
    setTimeout(() => n.close(), 3000)
    browserMsgType.value = 'success'
    browserMsg.value = 'Notification test envoyee sur cet appareil.'
  } catch (e) {
    browserMsgType.value = 'error'
    browserMsg.value = 'Impossible de generer une notification test.'
  }
}
</script>
<style scoped src="@/assets/styles/settings.css"></style>