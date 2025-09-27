<template>
  <div class="reset-page">
    <div class="reset-decor">
      <span class="orb orb--one"></span>
      <span class="orb orb--two"></span>
      <span class="orb orb--three"></span>
    </div>
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
        <a class="action-link" href="mailto:support@cova.fr">Besoin d'aide ? Contactez-nous</a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import axios from 'axios'
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
    await api.post(`/reset-password/${token}`, {
      password: password.value
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

<style scoped>
.reset-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 3rem 1.5rem;
  background: radial-gradient(circle at 10% 20%, #203b8a 0%, #0b1330 55%, #050815 100%);
  position: relative;
  overflow: hidden;
}

.reset-decor {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(0);
  opacity: 0.35;
  transform: translateZ(0);
}

.orb--one {
  width: 420px;
  height: 420px;
  background: linear-gradient(135deg, rgba(45, 100, 255, 0.8), rgba(34, 201, 255, 0.6));
  top: -120px;
  right: -120px;
}

.orb--two {
  width: 320px;
  height: 320px;
  background: linear-gradient(135deg, rgba(13, 83, 187, 0.75), rgba(91, 128, 255, 0.4));
  bottom: -140px;
  left: -140px;
}

.orb--three {
  width: 220px;
  height: 220px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.35), rgba(86, 140, 255, 0.35));
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.reset-card {
  position: relative;
  width: min(520px, 100%);
  padding: 3rem;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 30px 80px rgba(5, 16, 52, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.6);
  z-index: 1;
}

.card-brand {
  display: flex;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1.5rem;
}

.brand-logo {
  width: 58px;
  height: 58px;
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(30, 72, 194, 0.35);
}

.card-brand__eyebrow {
  margin: 0;
  text-transform: uppercase;
  font-size: 0.75rem;
  letter-spacing: 0.28rem;
  font-weight: 600;
  color: #1f3a8c;
}

.card-title {
  margin: 0.35rem 0 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: #122148;
  line-height: 1.25;
}

.card-intro {
  margin: 0 0 2rem;
  color: #3b486a;
  font-size: 1rem;
  line-height: 1.6;
}

.reset-form {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.form-label {
  font-weight: 600;
  color: #142550;
}

.input-shell {
  display: flex;
  align-items: center;
  border: 1px solid #d5dcf2;
  border-radius: 14px;
  padding: 0 0.5rem 0 0.85rem;
  background: #f5f7ff;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
}

.input-shell:focus-within {
  border-color: #3d64ff;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(61, 100, 255, 0.12);
}

.input-icon {
  font-size: 1.1rem;
  color: #3d4b82;
  margin-right: 0.65rem;
}

.form-control {
  flex: 1;
  border: none;
  background: transparent;
  font-size: 1rem;
  padding: 0.9rem 0.75rem;
  color: #131c3b;
}

.form-control:focus {
  box-shadow: none;
  outline: none;
}

.toggle-visibility {
  border: none;
  background: none;
  color: #4c5d8f;
  font-size: 1.1rem;
  display: grid;
  place-items: center;
  padding: 0.35rem 0.45rem;
  cursor: pointer;
}

.toggle-visibility:hover,
.toggle-visibility:focus {
  color: #1f3a8c;
}

.password-meter {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  margin-top: 0.25rem;
}

.password-meter__track {
  flex: 1;
  height: 6px;
  border-radius: 999px;
  background: #e1e6f6;
  overflow: hidden;
}

.password-meter__bar {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #f97316, #ef4444);
  transition: width 0.3s ease, background 0.3s ease;
}

.password-meter.is-fair .password-meter__bar {
  background: linear-gradient(90deg, #f97316, #f59e0b);
}

.password-meter.is-medium .password-meter__bar {
  background: linear-gradient(90deg, #22c55e, #16a34a);
}

.password-meter.is-strong .password-meter__bar,
.password-meter.is-excellent .password-meter__bar {
  background: linear-gradient(90deg, #3b82f6, #2563eb);
}

.password-meter__label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #2a3760;
}

.btn-submit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  width: 100%;
  border-radius: 16px;
  border: none;
  background: linear-gradient(90deg, #1d4ed8 0%, #2563eb 50%, #312e81 100%);
  color: #fff;
  font-weight: 600;
  font-size: 1.05rem;
  padding: 0.95rem 1rem;
  box-shadow: 0 16px 35px rgba(37, 99, 235, 0.35);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 24px 50px rgba(37, 99, 235, 0.45);
}

.btn-submit:disabled {
  opacity: 0.65;
  cursor: not-allowed;
  box-shadow: none;
}

.guidelines {
  margin: 2rem 0 1.5rem;
  padding: 1.25rem 1.5rem;
  border-radius: 18px;
  background: rgba(242, 245, 255, 0.95);
  border: 1px solid rgba(210, 220, 255, 0.9);
  color: #2d3a63;
  display: grid;
  gap: 0.5rem;
  list-style: none;
  font-size: 0.95rem;
}

.guidelines i {
  color: #2563eb;
  margin-right: 0.35rem;
}

.feedback {
  display: inline-flex;
  align-items: flex-start;
  gap: 0.5rem;
  border-radius: 14px;
  padding: 0.85rem 1rem;
  font-size: 0.95rem;
  margin-bottom: 0.75rem;
}

.feedback--error {
  background: rgba(248, 113, 113, 0.14);
  color: #b91c1c;
}

.feedback--success {
  background: rgba(110, 231, 183, 0.16);
  color: #047857;
}

.action-links {
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.action-link {
  color: #1f3a8c;
  font-weight: 600;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.action-link:hover,
.action-link:focus {
  text-decoration: underline;
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

@media (max-width: 640px) {
  .reset-card {
    padding: 2.25rem 1.75rem;
  }

  .card-title {
    font-size: 1.5rem;
  }

  .guidelines {
    padding: 1rem 1.15rem;
  }
}
</style>
