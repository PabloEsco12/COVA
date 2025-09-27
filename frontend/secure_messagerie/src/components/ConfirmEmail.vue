<template>
  <div class="reset-bg">
    <div class="reset-container animate__animated animate__fadeInDown">
      <img src="@/assets/logo_COVA.png" alt="Logo COVA" class="reset-logo" />
      <h2 class="reset-title mb-3">Confirmation d'email</h2>
      <Spinner v-if="loading" />
      <div v-else>
        <div v-if="error" class="alert alert-danger text-center">{{ error }}</div>
        <div v-if="success" class="alert alert-success text-center">{{ success }}</div>
        <router-link v-if="success" to="/login" class="btn btn-link mt-2 w-100">Se connecter</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { api } from '@/utils/api'
import { useRoute } from 'vue-router'
import Spinner from './Spinner.vue'

const route = useRoute()
const loading = ref(true)
const error = ref('')
const success = ref('')

onMounted(async () => {
  try {
    const res = await api.get(`/confirm-email/${route.params.token}`)
    success.value = res.data.message || "E-mail confirmé.";
  } catch (err) {
    error.value = err.response?.data?.error || 'Erreur inconnue'
  } finally {
    loading.value = false
  }
})
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
.alert {
  font-size: 1rem;
}
</style>
