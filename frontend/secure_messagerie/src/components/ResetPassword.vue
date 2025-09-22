<template>
  <div class="auth-page reset-page">
    <div class="auth-orb orb-primary"></div>
    <div class="auth-orb orb-secondary"></div>

    <div class="auth-grid">
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

      <section class="auth-card">
        <div class="auth-card__brand">
          <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="auth-card__logo" />
          <div>
            <p class="auth-card__subtitle">Regain d'accès</p>
            <h2 class="auth-card__title">Réinitialisez votre mot de passe</h2>
          </div>
        </div>

        <p class="auth-card__intro">
          Saisissez l'adresse e-mail professionnelle associée à votre espace COVA.
          Nous vous adresserons un lien sécurisé pour définir un nouveau mot de passe.
        </p>

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
              <p>Préparez votre nouveau mot de passe : 8 caractères minimum, avec chiffres et symboles.</p>
            </div>
          </div>
        </div>

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

        <div
          v-if="error"
          class="alert alert-danger text-center animate__animated animate__shakeX mt-3"
        >
          {{ error }}
        </div>

        <div
          v-if="success"
          class="alert alert-success text-center animate__animated animate__fadeInUp mt-3"
        >
          {{ success }}
        </div>

        <p class="auth-card__footer">
          Vous vous souvenez de vos identifiants ?
          <router-link to="/login">Retourner à la connexion</router-link>
        </p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const email = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)

async function handleReset() {
  error.value = ''
  success.value = ''
  loading.value = true
  try {
    await axios.post('http://localhost:5000/api/forgot-password', {
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

.reset-page::after {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(circle at 15% 20%, rgba(25, 89, 194, 0.18), transparent 45%),
    radial-gradient(circle at 85% 0%, rgba(90, 211, 245, 0.22), transparent 50%),
    radial-gradient(circle at 55% 100%, rgba(19, 72, 160, 0.15), transparent 55%);
  opacity: 0.85;
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
  width: 360px;
  height: 360px;
  top: -140px;
  right: -140px;
  background: radial-gradient(circle, rgba(25, 89, 194, 0.32) 0%, rgba(24, 60, 135, 0) 70%);
}

.orb-secondary {
  width: 300px;
  height: 300px;
  bottom: -160px;
  left: -120px;
  background: radial-gradient(circle, rgba(90, 211, 245, 0.34) 0%, rgba(90, 211, 245, 0) 70%);
}

.auth-grid {
  position: relative;
  z-index: 2;
  width: min(1120px, 100%);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 2.5rem;
  align-items: stretch;
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
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.18) 0%, rgba(9, 21, 58, 0.35) 100%);
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
  width: 2.4rem;
  height: 2.4rem;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.16);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
}

.auth-metrics {
  display: flex;
  gap: 2.5rem;
  margin-top: 0.5rem;
}

.auth-metrics strong {
  display: block;
  font-size: 1.8rem;
  font-weight: 700;
}

.auth-metrics span {
  font-size: 0.92rem;
  color: rgba(255, 255, 255, 0.8);
}

.auth-card {
  background: rgba(255, 255, 255, 0.94);
  border-radius: 36px;
  padding: clamp(2.4rem, 3vw, 3rem);
  box-shadow: 0 22px 60px rgba(17, 44, 108, 0.18);
  backdrop-filter: blur(18px);
  display: flex;
  flex-direction: column;
}

.auth-card__brand {
  display: flex;
  gap: 1.2rem;
  align-items: center;
  margin-bottom: 1.6rem;
}

.auth-card__logo {
  width: 58px;
  height: 58px;
  border-radius: 16px;
  box-shadow: 0 12px 30px rgba(25, 89, 194, 0.25);
}

.auth-card__subtitle {
  margin: 0;
  font-size: 0.92rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #1959c2;
  font-weight: 600;
}

.auth-card__title {
  margin: 0.35rem 0 0;
  font-size: 1.65rem;
  font-weight: 700;
  color: #101728;
}

.auth-card__intro {
  margin: 0 0 1.8rem;
  font-size: 0.98rem;
  color: rgba(16, 23, 40, 0.72);
  line-height: 1.55;
}

.reset-guidelines {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.2rem;
  margin-bottom: 2rem;
}

.reset-guidelines__item {
  display: flex;
  gap: 1rem;
  background: rgba(25, 89, 194, 0.08);
  border-radius: 20px;
  padding: 1.1rem 1.2rem;
  border: 1px solid rgba(25, 89, 194, 0.12);
}

.reset-guidelines__icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(25, 89, 194, 0.25) 0%, rgba(90, 211, 245, 0.4) 100%);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #0f2f6b;
  font-size: 1.2rem;
}

.reset-guidelines__item h3 {
  margin: 0 0 0.35rem;
  font-size: 1rem;
  color: #0f2f6b;
  font-weight: 600;
}

.reset-guidelines__item p {
  margin: 0;
  font-size: 0.85rem;
  color: rgba(16, 23, 40, 0.68);
  line-height: 1.45;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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

.auth-card__footer {
  margin-top: 2.25rem;
  text-align: center;
  font-size: 0.95rem;
  color: rgba(16, 23, 40, 0.75);
}

.auth-card__footer a {
  color: #1959c2;
  font-weight: 600;
  text-decoration: none;
  margin-left: 0.3rem;
}

.auth-card__footer a:hover,
.auth-card__footer a:focus {
  text-decoration: underline;
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

  .reset-guidelines {
    grid-template-columns: 1fr;
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
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 460px) {
  .auth-illustration {
    padding: 2rem 1.6rem;
  }

  .auth-feature-list li {
    font-size: 0.95rem;
  }

  .auth-metrics {
    gap: 1.5rem;
  }
}
</style>
