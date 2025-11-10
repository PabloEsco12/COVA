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
import { loginWithPassword } from '@/services/auth'
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
  } catch {
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

  const trimmed = code.value.trim()
  if (!trimmed || trimmed.length !== 6) {
    error.value = 'Veuillez indiquer un code TOTP valide.'
    return
  }

  loading.value = true
  try {
    const session = await loginWithPassword({
      email: pendingAuth.email,
      password: pendingAuth.password,
      totpCode: trimmed,
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

    sessionStorage.removeItem(pendingKey)
    router.replace('/dashboard')
  } catch (err) {
    const detail = err.response?.data?.detail || err.response?.data?.error
    if (typeof detail === 'string' && detail.trim()) {
      error.value = detail
    } else if (err.response?.data?.require_totp) {
      error.value = 'Code TOTP invalide. Reessayez avec le code le plus recent.'
      code.value = ''
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

<style scoped>
@import 'animate.css';

.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eef3fc 0%, #dfe7f8 40%, #eaf6ff 100%);
  padding: 3.5rem 1.5rem;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', 'Segoe UI', sans-serif;
}

.auth-page::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 20% 20%, rgba(25, 89, 194, 0.18), transparent 45%),
    radial-gradient(circle at 80% 0%, rgba(90, 211, 245, 0.2), transparent 50%),
    radial-gradient(circle at 50% 100%, rgba(19, 72, 160, 0.16), transparent 55%);
  opacity: 0.8;
  z-index: 1;
}

.auth-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(0);
  opacity: 0.8;
  z-index: 0;
}

.orb-primary {
  width: 340px;
  height: 340px;
  top: -120px;
  right: -120px;
  background: radial-gradient(circle, rgba(25, 89, 194, 0.35) 0%, rgba(24, 60, 135, 0) 70%);
}

.orb-secondary {
  width: 280px;
  height: 280px;
  bottom: -140px;
  left: -100px;
  background: radial-gradient(circle, rgba(90, 211, 245, 0.35) 0%, rgba(90, 211, 245, 0) 70%);
}

.auth-grid {
  position: relative;
  z-index: 2;
  width: min(1120px, 100%);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 2.5rem;
  align-items: center;
  justify-items: center;
}

.auth-grid > section {
  width: 100%;
}

.auth-illustration {
  position: relative;
  border-radius: 36px;
  overflow: hidden;
  background: linear-gradient(140deg, #183c87 0%, #1959c2 45%, #5ad3f5 100%);
  color: #fff;
  display: flex;
  align-items: flex-end;
  padding: clamp(2.5rem, 3vw, 3.5rem);
  box-shadow: 0 24px 60px rgba(20, 64, 140, 0.35);
}

.auth-illustration__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.15) 0%, rgba(9, 21, 58, 0.35) 100%);
  mix-blend-mode: screen;
  opacity: 0.75;
}

.auth-illustration__content {
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 1.6rem;
}

.auth-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.55rem 1.35rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  font-weight: 600;
  font-size: 0.95rem;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.auth-illustration h1 {
  font-size: clamp(2.1rem, 3vw, 2.7rem);
  line-height: 1.25;
  margin: 0;
}

.brand-text {
  color: #fff;
  text-shadow: 0 6px 24px rgba(0, 0, 0, 0.2);
}

.auth-illustration p {
  margin: 0;
  font-size: 1.05rem;
  color: rgba(255, 255, 255, 0.85);
}

.auth-feature-list {
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  margin: 0;
  padding: 0;
  list-style: none;
}

.auth-feature-list li {
  display: flex;
  align-items: flex-start;
  gap: 0.9rem;
  font-size: 0.98rem;
  line-height: 1.45;
}

.feature-icon {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.16);
  display: grid;
  place-items: center;
  font-size: 1.1rem;
}

.auth-card {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 36px;
  padding: clamp(2.4rem, 3vw, 3rem);
  box-shadow: 0 22px 60px rgba(17, 44, 108, 0.18);
  backdrop-filter: blur(18px);
  display: flex;
  flex-direction: column;
  gap: 2rem;
  position: relative;
  align-items: center;
  text-align: center;
  max-width: 480px;
  width: 100%;
}

.auth-card__brand {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-direction: column;
  margin-bottom: 1rem;
  width: 100%;
}

.auth-card__logo {
  width: 58px;
  height: 58px;
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(25, 89, 194, 0.25);
}

.auth-card__subtitle {
  margin: 0;
  font-size: 0.95rem;
  color: rgba(16, 23, 40, 0.65);
}

.auth-card__title {
  margin: 0;
  font-size: clamp(1.8rem, 3vw, 2.2rem);
  font-weight: 700;
  color: #101728;
}

.auth-context {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  padding: 0.75rem 1rem;
  border-radius: 12px;
  background: rgba(25, 89, 194, 0.08);
  color: #1959c2;
  font-weight: 600;
  max-width: fit-content;
  margin: 0 auto;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.4rem;
  width: 100%;
  max-width: 360px;
  margin: 0 auto;
}

.input-field {
  position: relative;
  display: flex;
  flex-direction: column;
}

.input-field__icon {
  position: absolute;
  top: 18px;
  left: 18px;
  color: #1959c2;
  font-size: 1.05rem;
  z-index: 2;
  opacity: 0.9;
}

.input-field__control {
  border: 1.5px solid rgba(25, 89, 194, 0.15);
  border-radius: 16px;
  padding: 1.05rem 1.1rem 1.05rem 3.2rem;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 12px 28px rgba(31, 82, 183, 0.08);
  font-size: 1rem;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.input-field__control:focus {
  outline: none;
  border-color: rgba(90, 211, 245, 0.8);
  box-shadow: 0 0 0 3px rgba(90, 211, 245, 0.25);
  transform: translateY(-1px);
}

.input-field__label {
  position: absolute;
  left: 3.2rem;
  top: 18px;
  color: rgba(16, 23, 40, 0.7);
  pointer-events: none;
  transition: 0.2s ease;
  font-weight: 500;
}

.input-field__control:focus + .input-field__label,
.input-field__control:not(:placeholder-shown) + .input-field__label {
  top: -0.6rem;
  left: 2.9rem;
  background: #fff;
  padding: 0 0.45rem;
  border-radius: 10px;
  font-size: 0.8rem;
  color: #1959c2;
  letter-spacing: 0.02em;
}

.input-field__hint {
  margin-top: 0.6rem;
  margin-left: 3.2rem;
  font-size: 0.78rem;
  color: rgba(16, 23, 40, 0.6);
}

.btn-auth {
  border: none;
  border-radius: 16px;
  padding: 0.95rem;
  background: linear-gradient(135deg, #1959c2 0%, #5ad3f5 100%);
  color: #fff;
  font-size: 1.05rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  width: 100%;
}

.btn-auth:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-auth:not(:disabled):hover,
.btn-auth:not(:disabled):focus {
  transform: translateY(-2px);
  box-shadow: 0 18px 35px rgba(25, 89, 194, 0.35);
}

.btn-auth-secondary {
  margin-top: 0.5rem;
  border: 1px solid rgba(25, 89, 194, 0.4);
  border-radius: 16px;
  padding: 0.9rem;
  background: transparent;
  color: #1959c2;
  font-size: 0.98rem;
  font-weight: 600;
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
  width: 100%;
}

.btn-auth-secondary:not(:disabled):hover,
.btn-auth-secondary:not(:disabled):focus {
  background: rgba(25, 89, 194, 0.08);
  transform: translateY(-1px);
}

.alert {
  border-radius: 12px;
  font-weight: 500;
}

@media (max-width: 1080px) {
  .auth-grid {
    gap: 2rem;
  }

  .auth-card__title {
    font-size: 1.55rem;
  }
}

@media (max-width: 992px) {
  .auth-grid {
    grid-template-columns: 1fr;
  }

  .auth-illustration,
  .auth-card {
    border-radius: 28px;
  }

  .auth-card {
    max-width: 540px;
    margin: 0 auto;
  }
}

@media (max-width: 640px) {
  .auth-page {
    padding: 2.5rem 1rem;
  }

  .auth-card {
    padding: 2.2rem 1.6rem;
  }

  .auth-card__brand {
    align-items: center;
  }

  .input-field__hint {
    margin-left: 0;
  }
}

@media (max-width: 460px) {
  .auth-illustration {
    padding: 2rem 1.6rem;
  }

  .auth-feature-list li {
    font-size: 0.95rem;
  }
}
</style>

