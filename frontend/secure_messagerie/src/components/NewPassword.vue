<template>
  <div class="reset-bg">
    <div class="reset-container animate__animated animate__fadeInDown">
      <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="reset-logo" />
      <h2 class="reset-title mb-3">Nouveau mot de passe</h2>
      <form @submit.prevent="handleNewPassword" class="reset-form">
        <div class="form-group mb-3">
          <div class="input-group">
            <span class="input-group-text"><i class="bi bi-lock-fill"></i></span>
            <input v-model="password" type="password" class="form-control" placeholder="Nouveau mot de passe" required>
          </div>
        </div>
        <div class="form-group mb-3">
          <div class="input-group">
            <span class="input-group-text"><i class="bi bi-lock-fill"></i></span>
            <input v-model="password2" type="password" class="form-control" placeholder="Répéter le mot de passe" required>
          </div>
        </div>
        <button type="submit" class="btn btn-gradient w-100" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm"></span>
          <span v-else>Changer le mot de passe</span>
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
import { useRoute } from 'vue-router'

const password = ref('')
const password2 = ref('')
const error = ref('')
const success = ref('')
const loading = ref(false)
const route = useRoute()

async function handleNewPassword() {
  error.value = ''
  success.value = ''
  loading.value = true
  if (!password.value || password.value !== password2.value) {
    error.value = "Les mots de passe ne correspondent pas."
    loading.value = false
    return
  }
  try {
    await axios.post('http://localhost:5000/api/reset-password/confirm', {
      token: route.query.token,  // ou route.params.token selon ton routing
      new_password: password.value,
    })
    success.value = "Mot de passe modifié. Tu peux te connecter !"
    password.value = password2.value = ''
  } catch (err) {
    error.value = err.response?.data?.error || 'Erreur inconnue'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Réutilise les styles de reset-bg et reset-container précédents */
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
