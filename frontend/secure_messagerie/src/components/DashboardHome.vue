<template>
  <div class="container py-4">
    <div class="row justify-content-center">
      <div class="col-lg-8">
        <div class="card p-5 shadow-lg text-center animate__animated animate__fadeIn">
          <h2 class="mb-2 display-5 fw-bold">Bienvenue sur COVA 🎉</h2>
          <p class="lead mb-4">
            Messagerie sécurisée, simple et rapide.<br>
            Retrouvez vos messages, contacts et notifications ici.
          </p>
          <img src="@/assets/logo.svg" alt="Logo COVA" style="width:80px; margin-bottom:20px;">
          <div class="row mt-3">
            <div class="col-6 col-md-3 mb-3">
              <router-link to="/dashboard/messages" class="btn btn-primary w-100">
                <i class="bi bi-chat-dots me-1"></i> Messages
              </router-link>
            </div>
            <div class="col-6 col-md-3 mb-3">
              <router-link to="/dashboard/contacts" class="btn btn-outline-secondary w-100">
                <i class="bi bi-people"></i> Contacts
              </router-link>
            </div>
            <div class="col-6 col-md-3 mb-3">
              <router-link to="/dashboard/devices" class="btn btn-outline-secondary w-100">
                <i class="bi bi-phone"></i> Appareils
              </router-link>
            </div>
            <div class="col-6 col-md-3 mb-3">
              <router-link to="/dashboard/settings" class="btn btn-outline-secondary w-100">
                <i class="bi bi-gear"></i> Paramètres
              </router-link>
            </div>
          </div>
          <div class="mt-4 text-muted small">
            Statut API :
            <span :class="apiOk ? 'text-success' : 'text-danger'">
              <i :class="apiOk ? 'bi bi-circle-fill' : 'bi bi-x-circle-fill'"></i>
              {{ apiOk ? 'Connecté' : 'Hors ligne' }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const apiOk = ref(false)

onMounted(async () => {
  try {
    await axios.get('http://localhost:5000/api/ping')
    apiOk.value = true
  } catch (e) {
    apiOk.value = false
  }
})
</script>
