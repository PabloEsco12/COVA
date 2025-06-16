<template>
  <div class="register-bg">
    <div class="register-container animate__animated animate__fadeInDown">
      <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="register-logo" />
      <h2 class="register-title mb-3">Créer un compte <span class="brand">COVA</span></h2>
      <form @submit.prevent="handleRegister" class="register-form">
        <div class="form-group mb-3">
          <div class="input-group">
            <span class="input-group-text"><i class="bi bi-person-fill"></i></span>
            <input v-model="pseudo" type="text" class="form-control" placeholder="Pseudo" required>
          </div>
        </div>
        <div class="form-group mb-3">
          <div class="input-group">
            <span class="input-group-text"><i class="bi bi-envelope-fill"></i></span>
            <input v-model="email" type="email" class="form-control" placeholder="Email" required>
          </div>
        </div>
        <div class="form-group mb-3">
          <div class="input-group">
            <span class="input-group-text"><i class="bi bi-lock-fill"></i></span>
            <input v-model="password" type="password" class="form-control" placeholder="Mot de passe" required>
          </div>
        </div>
        <button type="submit" class="btn btn-gradient w-100">S'inscrire</button>
      </form>
      <div v-if="error" class="alert alert-danger mt-3 text-center">{{ error }}</div>
      <div v-if="success" class="alert alert-success mt-3 text-center">{{ success }}</div>
      <router-link to="/login" class="btn btn-link mt-2 w-100">Déjà un compte ? Se connecter</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'

const pseudo = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const success = ref('')

async function handleRegister() {
  error.value = ''
  success.value = ''
  try {
    const res = await axios.post('http://localhost:5000/api/register', {
      pseudo: pseudo.value,
      email: email.value,
      password: password.value,
    })
    success.value = res.data.message || "Inscription réussie. Un e-mail de confirmation a été envoyé."
    pseudo.value = email.value = password.value = ''
  } catch (err) {
    error.value = err.response?.data?.error || 'Erreur inconnue'
  }
}
</script>

<style scoped>
.register-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #1959c2 0%, #162041 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.register-container {
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
.register-logo {
  width: 56px;
  margin-bottom: 12px;
  border-radius: 10px;
  box-shadow: 0 2px 12px #1959c2ad;
}
.register-title {
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
