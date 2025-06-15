<template>
  <div class="reset-bg">
    <div class="reset-container animate__animated animate__fadeInDown">
      <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="reset-logo" />
      <h2 class="reset-title mb-3">Mot de passe oublié ?</h2>
      <form @submit.prevent="handleReset" class="reset-form">
        <div class="form-group mb-3">
          <div class="input-group">
            <span class="input-group-text"><i class="bi bi-envelope-fill"></i></span>
            <input v-model="email" type="email" class="form-control" placeholder="Email" required>
          </div>
        </div>
        <button type="submit" class="btn btn-gradient w-100" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm"></span>
          <span v-else>Envoyer le lien de réinitialisation</span>
        </button>
      </form>
      <div v-if="error" class="alert alert-danger mt-3 text-center">{{ error }}</div>
      <div v-if="success" class="alert alert-success mt-3 text-center">{{ success }}</div>
      <router-link to="/login" class="btn btn-link mt-2 w-100">Retour à la connexion</router-link>
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
    await axios.post('http://localhost:5000/api/reset-password', {
      email: email.value,
    })
    success.value = "Si cet e-mail existe, tu recevras un lien de réinitialisation sous peu."
    email.value = ''
  } catch (err) {
    error.value = err.response?.data?.error || 'Erreur inconnue'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.reset-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #1959c2 0%, #162041 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.reset-container {
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
.reset-logo {
  width: 56px;
  margin-bottom: 12px;
  border-radius: 10px;
  box-shadow: 0 2px 12px #1959c2ad;
}
.reset-title {
  font-weight: 600;
  letter-spacing: 1px;
  color: #1b2845;
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
