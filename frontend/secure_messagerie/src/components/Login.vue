<template>
  <div class="login-bg">
    <div class="login-container">
      <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="login-logo" />
      <h2 class="login-title mb-3">Connexion à <span class="brand">COVA</span></h2>
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group mb-3">
          <div class="input-group">
            <span class="input-group-text"><i class="bi bi-envelope-fill"></i></span>
            <input v-model="email" type="email" class="form-control" placeholder="Email" required autocomplete="username">
          </div>
        </div>
        <div class="form-group mb-3">
          <div class="input-group">
            <span class="input-group-text"><i class="bi bi-lock-fill"></i></span>
            <input v-model="password" type="password" class="form-control" placeholder="Mot de passe" required autocomplete="current-password">
          </div>
        </div>
        <div class="form-group mb-3">
          <div class="input-group">
            <span class="input-group-text"><i class="bi bi-shield-lock-fill"></i></span>
            <input v-model="totp" type="text" class="form-control" placeholder="Code TOTP (si activé)">
          </div>
        </div>
        <button type="submit" class="btn btn-gradient w-100" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm"></span>
          <span v-else>Se connecter</span>
        </button>
      </form>
      <div v-if="error" class="alert alert-danger mt-3 text-center">{{ error }}</div>
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
/* Fond de la page login */
.login-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #1959c2 0%, #162041 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.login-container {
  background: rgba(255,255,255,0.14);
  border-radius: 24px;
  box-shadow: 0 8px 32px 0 rgba(31,38,135,0.25);
  backdrop-filter: blur(7px);
  -webkit-backdrop-filter: blur(7px);
  padding: 3rem 2rem 2rem 2rem;
  width: 100%;
  max-width: 410px;
  border: 1.5px solid rgba(255,255,255,0.12);
  text-align: center;
}
.login-logo {
  width: 56px;
  margin-bottom: 12px;
  border-radius: 10px;
  box-shadow: 0 2px 12px #1959c2ad;
}
.login-title {
  font-weight: 600;
  letter-spacing: 1px;
  color: #1b2845;
}
.brand {
  color: #1959c2;
  letter-spacing: 2px;
  font-weight: 700;
}
.btn-gradient {
  background: linear-gradient(90deg,#1959c2 0,#2157d3 100%);
  color: #fff;
  border: none;
  font-weight: 600;
  transition: box-shadow 0.3s;
}
.btn-gradient:hover {
  box-shadow: 0 4px 16px #1959c277;
  color: #fff;
}
.input-group-text {
  background: #e6e8f1;
  border: none;
}
input.form-control {
  border-left: 0;
  background: #fff;
  border-radius: 0 6px 6px 0;
}
.alert {
  font-size: 1rem;
}
</style>
