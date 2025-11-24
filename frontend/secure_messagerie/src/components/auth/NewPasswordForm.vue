<!-- src/components/auth/NewPasswordForm.vue -->
<template>
  <div class="reset-card animate__animated animate__fadeInUp">
    <div class="card-brand">
      <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="brand-logo" />
      <div>
        <p class="card-brand__eyebrow">Espace sécurisé COVA</p>
        <h1 class="card-title">Définissez votre nouveau mot de passe</h1>
      </div>
    </div>

    <p class="card-intro">
      Pour protéger vos échanges sensibles, choisissez un mot de passe robuste que vous n'utilisez nulle part
      ailleurs. Il sera effectif immédiatement après validation.
    </p>

    <form @submit.prevent="handleNewPassword" class="reset-form">
      <div class="form-field">
        <label for="password" class="form-label">Nouveau mot de passe</label>
        <div class="input-shell">
          <span class="input-icon bi bi-shield-lock-fill" aria-hidden="true"></span>
          <input
            id="password"
            v-model="password"
            :type="showPassword ? 'text' : 'password'"
            class="form-control"
            placeholder="••••••••"
            autocomplete="new-password"
            required
          />
          <button
            type="button"
            class="toggle-visibility"
            :aria-label="showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'"
            @click="showPassword = !showPassword"
          >
            <i :class="showPassword ? 'bi bi-eye-slash' : 'bi bi-eye'" aria-hidden="true"></i>
          </button>
        </div>
        <transition name="fade-slide">
          <div v-if="password" class="password-meter" :class="`is-${strengthLevel}`">
            <div class="password-meter__track">
              <span class="password-meter__bar" :style="{ width: strengthPercent }"></span>
            </div>
            <span class="password-meter__label">{{ strengthLabel }}</span>
          </div>
        </transition>
      </div>

      <div class="form-field">
        <label for="password-confirm" class="form-label">Confirmer le mot de passe</label>
        <div class="input-shell">
          <span class="input-icon bi bi-check2-circle" aria-hidden="true"></span>
          <input
            id="password-confirm"
            v-model="password2"
            :type="showPasswordConfirm ? 'text' : 'password'"
            class="form-control"
            placeholder="••••••••"
            autocomplete="new-password"
            required
          />
          <button
            type="button"
            class="toggle-visibility"
            :aria-label="showPasswordConfirm ? 'Masquer la confirmation du mot de passe' : 'Afficher la confirmation du mot de passe'"
            @click="showPasswordConfirm = !showPasswordConfirm"
          >
            <i :class="showPasswordConfirm ? 'bi bi-eye-slash' : 'bi bi-eye'" aria-hidden="true"></i>
          </button>
        </div>
      </div>

      <button type="submit" class="btn-submit" :disabled="isSubmitDisabled">
        <span v-if="loading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
        <span>{{ loading ? 'Mise à jour en cours…' : 'Mettre à jour le mot de passe' }}</span>
      </button>
    </form>

    <ul class="guidelines">
      <li><i class="bi bi-dot"></i>8 caractères minimum, 12 et plus idéalement.</li>
      <li><i class="bi bi-dot"></i>Incluez majuscules, minuscules, chiffres et symboles.</li>
      <li><i class="bi bi-dot"></i>Évitez les informations personnelles ou évidentes.</li>
    </ul>

    <transition name="fade-slide">
      <p v-if="error" class="feedback feedback--error">
        <i class="bi bi-exclamation-triangle-fill" aria-hidden="true"></i>
        <span>{{ error }}</span>
      </p>
    </transition>

    <transition name="fade-slide">
      <p v-if="success" class="feedback feedback--success">
        <i class="bi bi-check-circle-fill" aria-hidden="true"></i>
        <span>{{ success }}</span>
      </p>
    </transition>

    <div class="action-links">
      <router-link to="/login" class="action-link">Retourner à la connexion</router-link>
      <a class="action-link" href="mailto:support@covamessagerie.be">Besoin d'aide ? Contactez-nous</a>
    </div>
  </div>
</template>

<script setup>
// Formulaire de creation de nouveau mot de passe a partir d'un token recu par email.
import { computed, ref } from 'vue'
import { api } from '@/utils/api'
import { useRoute } from 'vue-router'

const password = ref('')
const password2 = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)
const showPassword = ref(false)
const showPasswordConfirm = ref(false)
const route = useRoute()

const passwordScore = computed(() => evaluateStrength(password.value))
const strengthPercent = computed(() => `${(passwordScore.value / 5) * 100}%`)
const strengthLevel = computed(() => {
  if (!password.value) return 'empty'
  if (passwordScore.value <= 1) return 'weak'
  if (passwordScore.value === 2) return 'fair'
  if (passwordScore.value === 3) return 'medium'
  if (passwordScore.value === 4) return 'strong'
  return 'excellent'
})
const strengthLabel = computed(() => {
  switch (strengthLevel.value) {
    case 'weak':
      return 'Sécurité très faible'
    case 'fair':
      return 'Peut mieux faire'
    case 'medium':
      return 'Sécurité correcte'
    case 'strong':
      return 'Très bon mot de passe'
    case 'excellent':
      return 'Mot de passe robuste'
    default:
      return 'Commencez à saisir votre mot de passe'
  }
})
const isSubmitDisabled = computed(() => loading.value || !password.value || !password2.value)

function evaluateStrength(value) {
  if (!value) {
    return 0
  }
  let score = 0
  if (value.length >= 12) {
    score += 2
  } else if (value.length >= 8) {
    score += 1
  }
  if (/[a-z]/.test(value)) score += 1
  if (/[A-Z]/.test(value)) score += 1
  if (/\d/.test(value)) score += 1
  if (/[^A-Za-z0-9]/.test(value)) score += 1
  return Math.min(score, 5)
}

async function handleNewPassword() {
  // Valide le token de reset et enregistre le nouveau mot de passe.
  error.value = ''
  success.value = ''

  if (!password.value) {
    error.value = 'Veuillez renseigner votre nouveau mot de passe.'
    return
  }
  if (password.value.length < 8) {
    error.value = 'Votre mot de passe doit comporter au moins 8 caractères.'
    return
  }
  if (password.value !== password2.value) {
    error.value = 'Les mots de passe saisis ne sont pas identiques.'
    return
  }

  const token = route.query?.token
  if (!token) {
    error.value = 'Le lien de réinitialisation est invalide ou a expiré.'
    return
  }

  loading.value = true
  try {
    await api.post(`/auth/reset-password`, {
      token,
      password: password.value,
    })
    success.value = 'Mot de passe mis à jour. Vous pouvez à présent vous connecter.'
    password.value = ''
    password2.value = ''
    showPassword.value = false
    showPasswordConfirm.value = false
  } catch (err) {
    error.value = err.response?.data?.error || 'Une erreur est survenue lors de la mise à jour.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped src="@/assets/styles/new-password.css"></style>


