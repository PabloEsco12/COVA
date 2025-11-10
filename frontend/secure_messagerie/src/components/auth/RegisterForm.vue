<script setup>
import { ref } from 'vue'
import { registerAccount, resendConfirmationEmail } from '@/services/auth'

const pseudo = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const success = ref('')
const successSubtitle = ref('')
const loading = ref(false)
const lastRegisteredEmail = ref('')
const resendLoading = ref(false)
const resendSuccessMessage = ref('')
const resendError = ref('')
const requiresConfirmation = ref(false)

async function handleRegister() {
  error.value = ''
  success.value = ''
  successSubtitle.value = ''
  loading.value = true
  try {
    const submittedEmail = email.value
    const res = await registerAccount({
      email: email.value,
      password: password.value,
      displayName: pseudo.value,
    })
    const confirmationRequired = Boolean(res.confirmation_url)
    success.value = 'Inscription finalisée avec succès !'
    if (confirmationRequired) {
      successSubtitle.value =
        `Nous venons d'envoyer un e-mail d'activation à ${submittedEmail}. ` +
        'Ouvrez-le puis cliquez sur « Confirmer mon adresse e-mail » dans les 30 prochaines minutes.'
    } else {
      successSubtitle.value = 'Vous pouvez désormais vous connecter immédiatement à votre espace sécurisé COVA.'
    }
    requiresConfirmation.value = confirmationRequired
    lastRegisteredEmail.value = confirmationRequired ? submittedEmail : ''
    resendSuccessMessage.value = ''
    resendError.value = ''
    pseudo.value = ''
    email.value = ''
    password.value = ''
  } catch (err) {
    const detail = err.response?.data?.detail || err.response?.data?.error
    error.value = detail || err.message || 'Erreur inconnue. Veuillez réessayer.'
    lastRegisteredEmail.value = ''
    resendSuccessMessage.value = ''
    resendError.value = ''
    requiresConfirmation.value = false
    successSubtitle.value = ''
  } finally {
    loading.value = false
  }
}

async function handleResend() {
  if (!requiresConfirmation.value || !lastRegisteredEmail.value) {
    resendError.value = 'Aucune inscription en attente de confirmation.'
    return
  }
  resendLoading.value = true
  resendSuccessMessage.value = ''
  resendError.value = ''
  try {
    await resendConfirmationEmail(lastRegisteredEmail.value)
    resendSuccessMessage.value = 'Nous avons renvoyé un e-mail de confirmation. Pensez à vérifier vos spams.'
  } catch (err) {
    const detail = err.response?.data?.detail || err.response?.data?.error || err.message
    resendError.value = detail || "Impossible d'envoyer le message pour le moment."
  } finally {
    resendLoading.value = false
  }
}
</script>

<template>
  <section class="auth-card">
    <div class="auth-card__brand">
      <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="auth-card__logo" />
      <div>
        <p class="auth-card__subtitle">Premiers pas sur la plateforme</p>
        <h2 class="auth-card__title">Créez votre accès sécurisé</h2>
      </div>
    </div>

    <p class="auth-card__intro">
      Renseignez vos informations professionnelles pour générer vos identifiants chiffrés.
      Vous recevrez un e-mail de confirmation afin d'activer votre compte.
    </p>

    <form @submit.prevent="handleRegister" class="auth-form">
      <div class="input-field">
        <span class="input-field__icon"><i class="bi bi-person-fill"></i></span>
        <input
          v-model="pseudo"
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

    <div v-if="error" class="alert alert-danger text-center mt-3">
      {{ error }}
    </div>

    <div v-if="success" class="auth-success mt-3">
      <div class="auth-success__icon">
        <i class="bi bi-check2-circle"></i>
      </div>
      <div class="auth-success__body">
        <p class="auth-success__title">{{ success }}</p>
        <p v-if="successSubtitle" class="auth-success__subtitle">{{ successSubtitle }}</p>
        <div v-if="requiresConfirmation && lastRegisteredEmail" class="resend-confirm">
          <p class="resend-confirm__text">
            Vous n'avez rien reçu ? Vérifiez vos spams ou renvoyez l'e-mail en un clic.
          </p>
          <button
            type="button"
            class="btn-resend-confirm"
            :disabled="resendLoading"
            @click="handleResend"
          >
            <span v-if="resendLoading" class="spinner-border spinner-border-sm"></span>
            <span v-else>Renvoyer l'e-mail de confirmation</span>
          </button>
          <p v-if="resendSuccessMessage" class="resend-confirm__success">{{ resendSuccessMessage }}</p>
          <p v-if="resendError" class="resend-confirm__error">{{ resendError }}</p>
        </div>
      </div>
    </div>

    <p class="auth-card__footer">
      Déjà inscrit ?
      <router-link to="/login">Revenir à la connexion</router-link>
    </p>
  </section>
</template>

<style scoped src="@/assets/styles/auth.css"></style>
