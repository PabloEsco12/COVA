<!-- src/components/auth/ResetPasswordForm.vue -->
<template>
  <!-- ===== Parcours de demande de reinitialisation ===== -->
  <div class="auth-grid">
    <!-- Colonne gauche: illustration rassurante -->
    <section class="auth-illustration">
      <div class="auth-illustration__overlay"></div>
      <div class="auth-illustration__content">
        <div class="auth-badge">
          <i class="bi bi-life-preserver me-2"></i>
          Assistance sécurisée
        </div>
        <h1>
          Restaurez votre accès à
          <span class="brand-text">COVA</span>
        </h1>
        <p>
          Une procédure guidée et chiffrée pour remettre votre messagerie souveraine
          sur les rails en quelques instants.
        </p>
        <ul class="auth-feature-list">
          <li>
            <span class="feature-icon"><i class="bi bi-envelope-check-fill"></i></span>
            Lien de réinitialisation signé et valable pendant 30 minutes.
          </li>
          <li>
            <span class="feature-icon"><i class="bi bi-shield-lock-fill"></i></span>
            Contrôles renforcés pour protéger vos échanges sensibles.
          </li>
          <li>
            <span class="feature-icon"><i class="bi bi-chat-dots-fill"></i></span>
            Équipe support disponible à tout moment pour vous accompagner.
          </li>
        </ul>
        <div class="auth-metrics">
          <div>
            <strong>&lt; 2 min</strong>
            <span>pour déclencher la procédure</span>
          </div>
          <div>
            <strong>24/7</strong>
            <span>support cybersécurité</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Colonne droite: formulaire de demande -->
    <section class="auth-card">
      <!-- Titre et rappel du contexte -->
      <div class="auth-card__brand">
        <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="auth-card__logo" />
        <div>
          <p class="auth-card__subtitle">Regain d'accès</p>
          <h2 class="auth-card__title">Réinitialisez votre mot de passe</h2>
        </div>
      </div>

      <!-- Explication rapide de la procedure -->
      <p class="auth-card__intro">
        Saisissez l'adresse e-mail professionnelle associée à votre espace COVA.
        Nous vous adresserons un lien sécurisé pour définir un nouveau mot de passe.
      </p>

      <!-- Conseils pour guider l'utilisateur avant l'envoi -->
      <div class="reset-guidelines">
        <div class="reset-guidelines__item">
          <span class="reset-guidelines__icon"><i class="bi bi-shield-check"></i></span>
          <div>
            <h3>Protection renforcée</h3>
            <p>Le lien transmis est unique, chiffré et expirable pour éviter tout abus.</p>
          </div>
        </div>
        <div class="reset-guidelines__item">
          <span class="reset-guidelines__icon"><i class="bi bi-lightning-charge"></i></span>
          <div>
            <h3>Procédure express</h3>
            <p>Préparez votre nouveau mot de passe : 8 caractères minimum, avec chiffres et symboles.</p>
          </div>
        </div>
      </div>

      <!-- Formulaire de saisie de l'email a reinitialiser -->
      <form @submit.prevent="handleReset" class="auth-form">
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

        <button type="submit" class="btn-auth" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm"></span>
          <span v-else>Envoyer le lien sécurisé</span>
        </button>
      </form>

      <!-- Retour en cas d'erreur serveur -->
      <div
        v-if="error"
        class="alert alert-danger text-center animate__animated animate__shakeX mt-3"
      >
        {{ error }}
      </div>

      <!-- Confirmation si le mail a ete envoye -->
      <div
        v-if="success"
        class="alert alert-success text-center animate__animated animate__fadeInUp mt-3"
      >
        {{ success }}
      </div>

      <!-- Raccourci retour connexion -->
      <p class="auth-card__footer">
        Vous vous souvenez de vos identifiants ?
        <router-link to="/login">Retourner à la connexion</router-link>
      </p>
    </section>
  </div>
</template>

<script setup>
// ===== Logique de demande de reset =====
import { ref } from 'vue'
import { api } from '@/utils/api'

// ===== Etats reactivs =====
const email = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

// ===== Soumission du formulaire de reset =====
async function handleReset() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    await api.post(`/auth/forgot-password`, {
      email: email.value,
    })
    success.value =
      "Si cette adresse est reconnue, un lien de réinitialisation vient d'être envoyé."
    email.value = ''
  } catch (err) {
    error.value = err.response?.data?.error || 'Une erreur inattendue est survenue.'
  } finally {
    loading.value = false
  }
}
</script>

<!-- on réutilise ton css -->
<!-- ===== Styles pour la page de reset ===== -->
<style scoped src="@/assets/styles/reset-password.css"></style>
