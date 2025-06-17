<template>
  <div class="login-bg-2025">
    <div class="login-glass">
      <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="login-logo-2025" />
      <h1 class="mb-1 text-gradient">Bienvenue sur <span class="brand-2025">COVA</span></h1>
      <p class="text-muted mb-4">Messagerie sécurisée & moderne</p>
      <form @submit.prevent="handleLogin" class="login-form-2025">
        <div class="form-group mb-4 input-effect">
          <span class="input-icon"><i class="bi bi-envelope-fill"></i></span>
          <input v-model="email" type="email" class="form-control glowing-input" placeholder=" " required autocomplete="username">
          <label>Email</label>
        </div>
        <div class="form-group mb-4 input-effect">
          <span class="input-icon"><i class="bi bi-lock-fill"></i></span>
          <input v-model="password" type="password" class="form-control glowing-input" placeholder=" " required autocomplete="current-password">
          <label>Mot de passe</label>
        </div>
        <div class="form-group mb-4 input-effect">
          <span class="input-icon"><i class="bi bi-shield-lock-fill"></i></span>
          <input v-model="totp" type="text" class="form-control glowing-input" placeholder=" " autocomplete="one-time-code">
          <label>Code TOTP (si activé)</label>
        </div>
        <button type="submit" class="btn btn-gradient-2025 w-100" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm"></span>
          <span v-else>Se connecter</span>
        </button>
      </form>
      <!-- Lien mot de passe oublié stylé -->
      <router-link 
        to="/reset-password"
        class="forgot-link mt-2 d-block text-center"
      >
        <i class="bi bi-question-circle me-1"></i>
        Mot de passe oublié ?
      </router-link>

      <div v-if="error" class="alert alert-danger mt-3 text-center animate__animated animate__shakeX">{{ error }}</div>
      <router-link to="/register" class="btn btn-link mt-2 w-100">Créer un compte</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const email = ref('')
const password = ref('')
const totp = ref('')
const error = ref('')
const loading = ref(false)
const router = useRouter()

onMounted(() => {
  if (localStorage.getItem('access_token')) {
    router.push('/dashboard')
  }
})

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    const res = await axios.post('http://localhost:5000/api/login', {
      email: email.value,
      password: password.value,
      code: totp.value,
    })
    localStorage.setItem('access_token', res.data.access_token)
    localStorage.setItem('refresh_token', res.data.refresh_token)
        localStorage.setItem('pseudo', res.data.user?.pseudo || '')

    try {
      const profile = await axios.get('http://localhost:5000/api/me', {
        headers: { Authorization: `Bearer ${res.data.access_token}` }
      })
      if (profile.data.avatar) {
        localStorage.setItem(
          'avatar_url',
          `http://localhost:5000/static/avatars/${profile.data.avatar}`
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
      error.value = "Veuillez saisir le code TOTP reçu sur votre application."
    } else if (err.response?.data?.error) {
      error.value = err.response.data.error
    } else {
      error.value = 'Erreur inconnue, réessayez.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
@import 'animate.css';

.login-bg-2025 {
  min-height: 100vh;
  background: linear-gradient(135deg, #23243a 0%, #183c87 35%, #5ad3f5 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}
.login-bg-2025::before {
  content: "";
  position: absolute;
  top: -200px; left: -150px; width: 400px; height: 400px;
  background: radial-gradient(circle, #5ad3f544 30%, transparent 70%);
  z-index: 1;
  filter: blur(18px);
}
.login-bg-2025::after {
  content: "";
  position: absolute;
  right: -180px; bottom: -180px; width: 350px; height: 350px;
  background: radial-gradient(circle, #183c87bb 30%, transparent 70%);
  z-index: 1;
  filter: blur(15px);
}

.login-glass {
  z-index: 2;
  width: 100%;
  max-width: 400px;
  padding: 2.5rem 2.5rem 1.5rem 2.5rem;
  background: rgba(255,255,255,0.13);
  border-radius: 30px;
  box-shadow: 0 8px 40px 0 #1348a030, 0 2px 16px 0 #0001;
  backdrop-filter: blur(14px);
  border: 1.5px solid rgba(255,255,255,0.18);
  text-align: center;
  position: relative;
}
.login-logo-2025 {
  width: 64px;
  margin-bottom: 14px;
  border-radius: 12px;
  box-shadow: 0 2px 24px #1959c2a0;
}
.text-gradient {
  background: linear-gradient(90deg,#1959c2 0,#5ad3f5 100%);
  color: transparent;
  -webkit-background-clip: text;
  background-clip: text;
}
.brand-2025 {
  letter-spacing: 1.5px;
  font-weight: 700;
  color: #183c87;
  background: none !important;
}

.login-form-2025 {
  margin-top: 1.2rem;
  text-align: left;
}

.input-effect {
  position: relative;
  margin-bottom: 1.8rem;
}
.input-icon {
  position: absolute;
  left: 13px; top: 12px;
  color: #1959c2cc;
  font-size: 1.17em;
  z-index: 4;
}
.glowing-input {
  padding-left: 2.2rem;
  border: 1.3px solid #ccd6f6;
  border-radius: 12px;
  transition: border-color 0.25s, box-shadow 0.25s;
  box-shadow: 0 2px 6px #1348a01a;
  font-size: 1.05em;
  background: rgba(255,255,255,0.87);
}
.glowing-input:focus {
  border-color: #5ad3f5;
  outline: none;
  box-shadow: 0 0 0 2px #5ad3f560;
}
.input-effect label {
  position: absolute;
  left: 2.2rem;
  top: 12px;
  color: #667;
  pointer-events: none;
  font-size: 1em;
  opacity: 0.82;
  transition: 0.18s cubic-bezier(0.4,0,0.2,1);
}
.input-effect input:focus + label,
.input-effect input:not(:placeholder-shown) + label {
  top: -0.8rem;
  left: 2.2rem;
  font-size: 0.90em;
  color: #1959c2;
  opacity: 1;
  background: #fff8;
  padding: 0 2px;
  border-radius: 4px;
}
.btn-gradient-2025 {
  background: linear-gradient(90deg,#1959c2 0,#5ad3f5 100%);
  color: #fff;
  border: none;
  font-weight: 600;
  transition: box-shadow 0.25s;
  border-radius: 13px;
  font-size: 1.13em;
  padding: 0.65em 0;
  letter-spacing: 1px;
}
.btn-gradient-2025:hover, .btn-gradient-2025:focus {
  box-shadow: 0 2px 20px #5ad3f580;
  color: #fff;
}

.forgot-link {
  color: #1959c2;
  font-weight: 500;
  font-size: 1.05em;
  text-decoration: none;
  transition: color 0.18s;
  margin-bottom: 8px;
}
.forgot-link:hover,
.forgot-link:focus {
  color: #183c87;
  text-decoration: underline;
}

.alert {
  font-size: 1rem;
}
@media (max-width: 600px) {
  .login-glass { padding: 2rem 1rem 1rem 1rem; }
}
</style>
