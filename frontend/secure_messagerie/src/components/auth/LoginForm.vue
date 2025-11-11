<!-- src/components/auth/LoginForm.vue -->
<template>
  <section class="auth-card">
    <div class="auth-card__brand">
      <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="auth-card__logo" />
      <div>
        <p class="auth-card__subtitle">Heureux de vous revoir</p>
        <h2 class="auth-card__title">Connectez-vous à votre espace sécurisé</h2>
      </div>
    </div>

    <form @submit.prevent="handleLogin" class="auth-form">
      <div class="input-field">
        <span class="input-field__icon"><i class="bi bi-envelope-fill"></i></span>
        <input
          v-model="email"
          type="email"
          class="input-field__control"
          placeholder=" "
          required
          autocomplete="username"
        >
        <label class="input-field__label">Adresse e-mail professionnelle</label>
      </div>

      <div class="input-field">
        <span class="input-field__icon"><i class="bi bi-lock-fill"></i></span>
        <input
          v-model="password"
          type="password"
          class="input-field__control"
          placeholder=" "
          required
          autocomplete="current-password"
        >
        <label class="input-field__label">Mot de passe</label>
        <router-link to="/reset-password" class="input-field__action">
          <i class="bi bi-question-circle"></i>
          Mot de passe oublié ?
        </router-link>
      </div>

      <button type="submit" class="btn-auth" :disabled="loading">
        <span v-if="loading" class="spinner-border spinner-border-sm"></span>
        <span v-else>Se connecter</span>
      </button>
    </form>

    <div
      v-if="error"
      class="auth-alert animate__animated animate__shakeX mt-3"
      role="alert"
    >
      <div class="auth-alert__icon">
        <i class="bi bi-exclamation-octagon-fill"></i>
      </div>
      <div class="auth-alert__content">
        <p class="auth-alert__title">{{ error }}</p>
        <p v-if="errorHint" class="auth-alert__hint">{{ errorHint }}</p>
        <router-link
          v-if="!showResend"
          to="/reset-password"
          class="auth-alert__action"
        >
          <i class="bi bi-arrow-counterclockwise"></i>
          Réinitialiser mon mot de passe
        </router-link>
      </div>
    </div>

    <div v-if="showResend" class="resend-card mt-3">
      <p class="resend-card__text">
        Vous n'avez pas reçu l'e-mail de confirmation ? Cliquez ci-dessous pour en recevoir un nouveau.
      </p>
      <button
        type="button"
        class="btn-resend"
        :disabled="resendLoading"
        @click="handleResend"
      >
        <span v-if="resendLoading" class="spinner-border spinner-border-sm"></span>
        <span v-else>Renvoyer l'e-mail de confirmation</span>
      </button>
      <p v-if="resendSuccess" class="resend-card__success">
        Un nouvel e-mail vient d'être envoyé. Pensez à vérifier vos spams.
      </p>
      <p v-if="resendError" class="resend-card__error">{{ resendError }}</p>
    </div>

    <p class="auth-card__footer">
      Pas encore de compte ?
      <router-link to="/register">Rejoindre la plateforme</router-link>
    </p>
  </section>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { api } from '@/utils/api'
import { loginWithPassword } from '@/services/auth'
import { useRouter, useRoute } from 'vue-router'

const email = ref('')
const password = ref('')
const error = ref('')
const errorHint = ref('')
const loading = ref(false)
const showResend = ref(false)
const resendLoading = ref(false)
const resendSuccess = ref(false)
const resendError = ref('')
const router = useRouter()
const route = useRoute()

onMounted(() => {
  // si déjà connecté -> dashboard
  if (localStorage.getItem('access_token')) {
    router.push('/dashboard')
  }
})

watch(
  () => route.query.reason,
  (reason) => {
    if (!reason) return
    const reasonValue = Array.isArray(reason) ? reason[0] : reason
    applyLogoutReason(reasonValue)
    clearReasonQuery()
  },
  { immediate: true },
)

function setError(message, hint = '') {
  error.value = message
  errorHint.value = hint
}

const logoutReasons = {
  'session-expired': {
    title: 'Votre session a expiré.',
    hint: 'Reconnectez-vous pour reprendre vos conversations sécurisées.',
  },
  'invalid-token': {
    title: 'Votre authentification n’est plus valide.',
    hint: 'Merci de vous reconnecter pour sécuriser votre accès.',
  },
}

function applyLogoutReason(reason) {
  const payload = logoutReasons[reason]
  if (!payload) return
  setError(payload.title, payload.hint)
  showResend.value = false
}

function clearReasonQuery() {
  try {
    const nextQuery = { ...route.query }
    delete nextQuery.reason
    router.replace({ path: route.path, query: nextQuery })
  } catch {
    // ignore
  }
}

async function handleLogin() {
  setError('')
  showResend.value = false
  resendError.value = ''
  resendSuccess.value = false
  loading.value = true
  try {
    const session = await loginWithPassword({
      email: email.value,
      password: password.value,
    })

    const user = session?.user || null
    const profile = user?.profile || null
    const displayName = profile?.display_name || user?.email || 'Utilisateur'

    if (displayName) {
      localStorage.setItem('pseudo', displayName)
    } else {
      localStorage.removeItem('pseudo')
    }

    if (profile?.avatar_url) {
      localStorage.setItem('avatar_url', profile.avatar_url)
    } else {
      localStorage.removeItem('avatar_url')
    }

    router.push('/dashboard')
  } catch (err) {
    // cas TOTP
    if (err.response?.data?.require_totp) {
      sessionStorage.setItem(
        'pending_totp',
        JSON.stringify({
          email: email.value,
          password: password.value,
        }),
      )
      loading.value = false
      router.push('/login/totp')
      return
    }

    const detailRaw = err.response?.data?.error || err.response?.data?.detail
    const detail = typeof detailRaw === 'string' ? detailRaw : ''
    const lowerDetail = detail.toLowerCase()

    if (lowerDetail === 'email not confirmed') {
      setError(
        'Veuillez confirmer votre adresse e-mail avant de vous connecter.',
        'Nous pouvons vous renvoyer le lien de validation ci-dessous.',
      )
      showResend.value = true
    } else if (
      lowerDetail.includes('incorrect') ||
      lowerDetail.includes('invalid credentials') ||
      lowerDetail.includes('invalid username or password') ||
      err.response?.status === 401
    ) {
      setError(
        'Identifiants incorrects.',
        'Vérifiez l’orthographe de votre e-mail et de votre mot de passe ou utilisez le lien « Mot de passe oublié ».',
      )
      showResend.value = false
    } else if (detail) {
      setError(detail)
      showResend.value = false
    } else {
      setError('Une erreur est survenue. Veuillez réessayer.')
      showResend.value = false
    }
  } finally {
    loading.value = false
  }
}

async function handleResend() {
  if (!email.value) {
    resendError.value = 'Veuillez indiquer votre adresse e-mail.'
    return
  }
  resendLoading.value = true
  resendSuccess.value = false
  resendError.value = ''
  try {
    await api.post(`/auth/resend-confirmation`, { email: email.value })
    resendSuccess.value = true
  } catch (err) {
    const detail = err.response?.data?.detail || err.response?.data?.error || err.message
    resendError.value = detail || "Impossible d'envoyer le message pour le moment."
  } finally {
    resendLoading.value = false
  }
}
</script>

<style scoped src="@/assets/styles/login.css"></style>
