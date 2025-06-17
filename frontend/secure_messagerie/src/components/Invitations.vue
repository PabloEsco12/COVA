<template>
  <div class="invitations-container card shadow-lg mx-auto p-4">
    <div class="d-flex align-items-center mb-3">
      <i class="bi bi-envelope-paper fs-2 text-primary me-3"></i>
      <div>
        <h3 class="mb-0 fw-bold">Invitations</h3>
        <small class="text-muted">Gère tes invitations reçues</small>
      </div>
      <div class="ms-auto">
        <button class="btn btn-outline-primary btn-sm" @click="refresh">
          <i class="bi bi-arrow-clockwise"></i>
        </button>
      </div>
    </div>
    <div v-if="loading" class="text-center py-5">
      <span class="spinner-border text-primary"></span>
    </div>
    <div v-else>
      <div v-if="invitations.length === 0" class="text-center text-muted py-5">
        <i class="bi bi-envelope-open display-4"></i>
        <div>Aucune invitation</div>
      </div>
      <ul class="list-group list-group-flush">
        <li
          v-for="inv in invitations"
          :key="inv.id_contact"
          class="list-group-item d-flex align-items-center justify-content-between"
        >
          <div>
            <div class="fw-semibold">
              {{ inv.pseudo || `Utilisateur #${inv.demandeur}` }}
            </div>
            <div class="text-muted small">{{ inv.email }}</div>
          </div>
          <div>
            <button class="btn btn-success btn-sm me-2" @click="respond(inv.id_contact, 'accepted')">
              <i class="bi bi-check"></i>
            </button>
            <button class="btn btn-outline-danger btn-sm" @click="respond(inv.id_contact, 'blocked')">
              <i class="bi bi-x"></i>
            </button>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const invitations = ref([])
const loading = ref(true)

async function fetchInvitations() {
  loading.value = true
  try {
    const res = await axios.get('http://localhost:5000/api/contacts/invitations', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    invitations.value = res.data || []
  } catch {
    invitations.value = []
  } finally {
    loading.value = false
  }
}

async function respond(id, statut) {
  loading.value = true
  try {
    await axios.patch(`http://localhost:5000/api/contacts/${id}`, { statut }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    await fetchInvitations()
  } catch (e) {
    // ignore error display for now
  } finally {
    loading.value = false
  }
}

function refresh() {
  fetchInvitations()
}

onMounted(fetchInvitations)
</script>

<style scoped>
.invitations-container {
  max-width: 580px;
  margin: 2rem auto;
  background: #fff;
  border-radius: 18px;
}

.list-group-item {
  border: none;
  border-bottom: 1px solid #f3f4f7;
  background: transparent;
}
.list-group-item:last-child {
  border-bottom: none;
}
</style>
