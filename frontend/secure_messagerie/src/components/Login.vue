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
import axios from 'axios'
import { api, backendBase } from '@/utils/api'
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
    const res = await api.post(`/login`, {
      email: email.value,
      password: password.value,
    })
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
    localStorage.setItem('pseudo', res.data.user?.pseudo || '')
    localStorage.setItem('user_id', res.data.user?.id || '')
    localStorage.setItem('user_email', res.data.user?.email || '')

    try {
      const profile = await api.get(`/me`)
      if (profile.data.avatar) {
        localStorage.setItem(
          'avatar_url',
          `${backendBase}/static/avatars/${profile.data.avatar}`
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
      sessionStorage.setItem('pending_totp', JSON.stringify({
        email: email.value,
        password: password.value,
      }))
      loading.value = false
      router.push('/login/totp')
      return
    } else if (err.response?.data?.error) {
      error.value = err.response.data.error
    } else {
      error.value = 'Erreur inconnue, reessayez.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped src="../styles/components/Login.css"></style>
