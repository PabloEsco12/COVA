<template>
  <div class="auth-page">
    <div class="auth-orb orb-primary"></div>
    <div class="auth-orb orb-secondary"></div>
    <div class="auth-grid">
      <section class="auth-illustration">
        <div class="auth-illustration__overlay"></div>
        <div class="auth-illustration__content">
          <div class="auth-badge">
            <i class="bi bi-shield-lock-fill me-2"></i>
            Verification en deux etapes
          </div>
          <h1>
            Confirmez votre identite avec
            <span class="brand-text">COVA</span>
          </h1>
          <p>
            Saisissez le code genere par votre application d’authentification afin de finaliser la connexion.
          </p>
          <ul class="auth-feature-list">
            <li>
              <span class="feature-icon"><i class="bi bi-shield-check"></i></span>
              Protection additionnelle pour votre messagerie securisee.
            </li>
            <li>
              <span class="feature-icon"><i class="bi bi-phone"></i></span>
              Codes disponibles sur votre application mobile ou desktop favourite.
            </li>
            <li>
              <span class="feature-icon"><i class="bi bi-clock-history"></i></span>
              Chaque code expire rapidement, assurez-vous d’utiliser le plus recent.
            </li>
          </ul>
        </div>
      </section>

      <section class="auth-card">
        <div class="auth-card__brand">
          <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="auth-card__logo" />
          <div>
            <p class="auth-card__subtitle">Verification requise</p>
            <h2 class="auth-card__title">Entrez votre code TOTP</h2>
          </div>
        </div>

        <div class="auth-context" v-if="userEmail">
          <i class="bi bi-envelope"></i>
          <span>{{ userEmail }}</span>
        </div>

        <form @submit.prevent="handleTotp" class="auth-form">
          <div class="input-field">
            <span class="input-field__icon"><i class="bi bi-shield-lock-fill"></i></span>
            <input
              v-model="code"
              type="text"
              inputmode="numeric"
              pattern="[0-9]*"
              maxlength="6"
              class="input-field__control"
              placeholder=" "
              autocomplete="one-time-code"
              required
            >
            <label class="input-field__label">Code TOTP</label>
            <small class="input-field__hint">Saisissez le code a 6 chiffres affiche par votre application.</small>
          </div>

          <button type="submit" class="btn-auth" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm"></span>
            <span v-else>Valider et continuer</span>
          </button>

          <button
            type="button"
            class="btn-auth-secondary"
            :disabled="loading"
            @click="cancelTotp"
          >
            Retour a la connexion
          </button>
        </form>

        <div v-if="error" class="alert alert-danger text-center animate__animated animate__shakeX mt-3">
          {{ error }}
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { api, backendBase } from '@/utils/api'
import { useRouter } from 'vue-router'

const code = ref('')
const error = ref('')
const loading = ref(false)
const userEmail = ref('')
const router = useRouter()

const pendingKey = 'pending_totp'
let pendingAuth = null

onMounted(() => {
  const raw = sessionStorage.getItem(pendingKey)
  if (!raw) {
    router.replace('/login')
    return
  }

  try {
    const parsed = JSON.parse(raw)
    if (!parsed?.email || !parsed?.password) {
      throw new Error('pending login missing data')
    }
    pendingAuth = parsed
    userEmail.value = parsed.email
  } catch (e) {
    sessionStorage.removeItem(pendingKey)
    router.replace('/login')
  }
})

async function handleTotp() {
  error.value = ''
  if (!pendingAuth) {
    router.replace('/login')
    return
  }

  if (!code.value.trim()) {
    error.value = 'Merci de saisir votre code TOTP.'
    return
  }

  loading.value = true
  try {
    const res = await api.post(`/login`, {
      email: pendingAuth.email,
      password: pendingAuth.password,
      code: code.value.trim(),
    })

    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    localStorage.setItem('pseudo', res.data.user?.pseudo || '')
    localStorage.setItem('user_id', res.data.user?.id || '')
    localStorage.setItem('user_email', res.data.user?.email || '')

    sessionStorage.removeItem(pendingKey)

    try {
      const profile = await api.get(`/me`)
      if (profile.data.avatar) {
        localStorage.setItem(
          'avatar_url',
          `${backendBase}/static/avatars/${profile.data.avatar}`,
        )
      } else {
        localStorage.removeItem('avatar_url')
      }
    } catch (e) {
      // ignore profile fetch errors
    }

    router.push('/dashboard')
  } catch (err) {
    if (err.response?.data?.require_totp) {
      error.value = 'Code TOTP invalide. Reessayez avec le code le plus recent.'
      code.value = ''
    } else if (err.response?.data?.error) {
      error.value = err.response.data.error
    } else {
      error.value = 'Erreur inconnue, reessayez.'
    }
  } finally {
    loading.value = false
  }
}

function cancelTotp() {
  sessionStorage.removeItem(pendingKey)
  router.push('/login')
}
</script>

<style scoped src="../styles/components/LoginTotp.css"></style>


