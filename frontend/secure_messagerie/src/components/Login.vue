<template>
  <div class="auth-page">
    <div class="auth-orb orb-primary"></div>
    <div class="auth-orb orb-secondary"></div>
    <div class="auth-grid">
      <section class="auth-illustration">
        <div class="auth-illustration__overlay"></div>
        <div class="auth-illustration__content">
          <div class="auth-badge">
            <i class="bi bi-shield-check me-2"></i>
            Messagerie souveraine
          </div>
          <h1>
            Collaborez en toute confiance avec
            <span class="brand-text">COVA</span>
          </h1>
          <p>
            Centralisez les échanges sensibles de votre organisation dans une interface
            moderne, sûre et pensée pour les équipes exigeantes.
          </p>
          <ul class="auth-feature-list">
            <li>
              <span class="feature-icon"><i class="bi bi-lock-fill"></i></span>
              Chiffrement de bout en bout et conformité RGPD.
            </li>
            <li>
              <span class="feature-icon"><i class="bi bi-lightning-charge-fill"></i></span>
              Notifications en temps réel et canaux dédiés.
            </li>
            <li>
              <span class="feature-icon"><i class="bi bi-people-fill"></i></span>
              Collaboration fluide entre équipes internes et partenaires.
            </li>
          </ul>
          <div class="auth-metrics">
            <div>
              <strong>+250</strong>
              <span>équipes actives</span>
            </div>
            <div>
              <strong>24/7</strong>
              <span>support dédié</span>
            </div>
          </div>
        </div>
      </section>

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
              Mot de passe oublié ?
            </router-link>
          </div>

          <button type="submit" class="btn-auth" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm"></span>
            <span v-else>Se connecter</span>
          </button>
        </form>

        <div v-if="error" class="alert alert-danger text-center animate__animated animate__shakeX mt-3">
          {{ error }}
        </div>

        <p class="auth-card__footer">
          Pas encore de compte ?
          <router-link to="/register">Rejoindre la plateforme</router-link>
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/utils/api'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const router = useRouter()
// Normalize API base so it always ends with '/api'
// Use centralized API base + backend origin

onMounted(() => {
  if (localStorage.getItem('access_token')) {
    router.push('/dashboard')
  }
})

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const payload = new URLSearchParams({
      username: email.value,
      password: password.value,
    })
    const res = await api.post('/auth/token', payload, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    localStorage.setItem('access_token', res.data.access_token)

    try {
      const profile = await api.get('/auth/me')
      localStorage.setItem('user_id', profile.data.id || '')
      localStorage.setItem('user_email', profile.data.email || '')
      localStorage.setItem('pseudo', profile.data.display_name || '')
      localStorage.removeItem('avatar_url')
    } catch (e) {
      // ignore profile fetch errors
    }
    router.push('/dashboard')
  } catch (err) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      error.value = detail
    } else {
      error.value = 'Erreur inconnue, reessayez.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped src="../styles/components/Login.css"></style>
