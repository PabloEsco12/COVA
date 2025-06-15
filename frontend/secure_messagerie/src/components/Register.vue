<template>
  <div class="container mt-5">
    <div class="row justify-content-center">
      <div class="col-md-4">
        <div class="card p-4 shadow">
          <h2 class="mb-3 text-center">Créer un compte SecureChat</h2>
          <form @submit.prevent="handleRegister">
            <div class="mb-3">
              <input v-model="pseudo" type="text" class="form-control" placeholder="Pseudo" required>
            </div>
            <div class="mb-3">
              <input v-model="email" type="email" class="form-control" placeholder="Email" required>
            </div>
            <div class="mb-3">
              <input v-model="password" type="password" class="form-control" placeholder="Mot de passe" required>
            </div>
            <button type="submit" class="btn btn-success w-100">S'inscrire</button>
          </form>
          <div v-if="error" class="alert alert-danger mt-3">{{ error }}</div>
          <div v-if="success" class="alert alert-success mt-3">{{ success }}</div>
          <router-link to="/login" class="btn btn-link mt-2 w-100">Déjà un compte ? Se connecter</router-link>
        </div>
      </div>
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
    success.value = res.data.message || "Inscription réussie. Vérifiez vos emails pour confirmer."
    pseudo.value = email.value = password.value = ''
  } catch (err) {
    error.value = err.response?.data?.error || 'Erreur inconnue'
  }
}
</script>
