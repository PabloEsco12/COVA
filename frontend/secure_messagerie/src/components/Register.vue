<template>
  <div class="auth-page signup-page">
    <div class="auth-orb orb-primary"></div>
    <div class="auth-orb orb-secondary"></div>

    <div class="auth-grid">
      <section class="auth-illustration">
        <div class="auth-illustration__overlay"></div>
        <div class="auth-illustration__content">
          <div class="auth-badge">
            <i class="bi bi-stars me-2"></i>
            Onboarding maîtrisé
          </div>
          <h1>
            Lancez votre espace collaboratif
            <span class="brand-text">COVA</span>
          </h1>
          <p>
            Déployez en toute simplicité un environnement souverain pour vos équipes.
            Nous accompagnons chaque organisation vers un démarrage sécurisé et fluide.
          </p>
          <ul class="auth-feature-list">
            <li>
              <span class="feature-icon"><i class="bi bi-person-badge-fill"></i></span>
              Validation des identités et contrôle des accès à la volée.
            </li>
            <li>
              <span class="feature-icon"><i class="bi bi-diagram-3-fill"></i></span>
              Espaces partagés, canaux projets et archivage automatique.
            </li>
            <li>
              <span class="feature-icon"><i class="bi bi-headset"></i></span>
              Experts COVA dédiés pour configurer vos règles de sécurité.
            </li>
          </ul>
          <div class="auth-metrics">
            <div>
              <strong>&lt; 5 min</strong>
              <span>pour activer votre équipe</span>
            </div>
            <div>
              <strong>99,9%</strong>
              <span>disponibilité garantie</span>
            </div>
          </div>
        </div>
      </section>

      <section class="auth-card">
        <div class="auth-card__brand">
          <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="auth-card__logo" />
          <div>
            <p class="auth-card__subtitle">Premiers pas sur la plateforme</p>
            <h2 class="auth-card__title">Créez votre accès sécurisé</h2>
          </div>
        </div>

        <p class="auth-card__intro">
          Renseignez vos informations professionnelles pour générer vos identifiants
          chiffrés. Vous recevrez un e-mail de confirmation afin d'activer votre
          compte.
        </p>

        <form @submit.prevent="handleRegister" class="auth-form">
          <div class="input-field">
            <span class="input-field__icon"><i class="bi bi-person-fill"></i></span>
            <input
              v-model="displayName"
              type="text"
              class="input-field__control"
              placeholder=" "
              required
              autocomplete="nickname"
            >
            <label class="input-field__label">Nom d'affichage</label>
          </div>

          <div class="input-field">
            <span class="input-field__icon"><i class="bi bi-envelope-fill"></i></span>
            <input
              v-model="email"
              type="email"
              class="input-field__control"
              placeholder=" "
              required
              autocomplete="email"
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
              minlength="8"
              autocomplete="new-password"
            >
            <label class="input-field__label">Mot de passe</label>
            <small class="input-field__hint">8 caractères minimum, combinez lettres, chiffres et symboles.</small>
          </div>

          <div class="auth-legal">
            En créant un compte, vous acceptez la charte de sécurité et de confidentialité COVA.
          </div>

          <button type="submit" class="btn-auth" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm"></span>
            <span v-else>Créer mon compte</span>
          </button>
        </form>

        <div v-if="error" class="alert alert-danger text-center animate__animated animate__shakeX mt-3">
          {{ error }}
        </div>

        <div
          v-if="success"
          class="alert alert-success text-center animate__animated animate__fadeInUp mt-3"
        >
          {{ success }}
        </div>

        <p class="auth-card__footer">
          Déjà inscrit ?
          <router-link to="/login">Revenir à la connexion</router-link>
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '@/utils/api'

const displayName = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    const payload = {
      email: email.value.trim(),
      password: password.value,
      display_name: displayName.value.trim() || null,
    }
    const res = await api.post('/auth/register', payload)
    success.value = `Inscription reussie pour ${res.data.email}. Vous pouvez maintenant vous connecter.`
    displayName.value = ''
    email.value = ''
    password.value = ''
  } catch (err) {
    const detail = err.response?.data?.detail
    if (typeof detail === 'string') {
      error.value = detail
    } else if (Array.isArray(detail)) {
      error.value = detail.map((item) => item.msg || JSON.stringify(item)).join(', ')
    } else {
      error.value = 'Erreur inconnue. Veuillez reessayer.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped src="../styles/components/Register.css"></style>
