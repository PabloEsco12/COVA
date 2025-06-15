<template>
  <div class="contacts-container card shadow-lg mx-auto p-4">
    <div class="d-flex align-items-center mb-3">
      <i class="bi bi-people fs-2 text-primary me-3"></i>
      <div>
        <h3 class="mb-0 fw-bold">Contacts</h3>
        <small class="text-muted">Gère ta liste de contacts COVA</small>
      </div>
      <div class="ms-auto">
        <button class="btn btn-outline-primary btn-sm" @click="refresh">
          <i class="bi bi-arrow-clockwise"></i>
        </button>
      </div>
    </div>
    <div class="mb-3">
      <div class="input-group">
        <input v-model="search" type="text" class="form-control" placeholder="Rechercher un contact...">
        <button class="btn btn-outline-success" @click="showAddModal = true">
          <i class="bi bi-person-plus"></i> Ajouter
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-5">
      <span class="spinner-border text-primary"></span>
    </div>

    <div v-else>
      <div v-if="filteredContacts.length === 0" class="text-center text-muted py-5">
        <i class="bi bi-emoji-frown display-4"></i>
        <div>Aucun contact trouvé</div>
      </div>
      <ul class="list-group list-group-flush">
        <li
          v-for="contact in filteredContacts"
          :key="contact.id"
          class="list-group-item d-flex align-items-center justify-content-between"
        >
          <div class="d-flex align-items-center">
            <i class="bi bi-person-circle fs-3 text-secondary me-2"></i>
            <div>
              <div class="fw-semibold">{{ contact.pseudo }}</div>
              <div class="text-muted small">{{ contact.email }}</div>
            </div>
          </div>
          <div>
            <span v-if="contact.statut === 'accepted'" class="badge bg-success me-2">Ami</span>
            <span v-else-if="contact.statut === 'pending'" class="badge bg-warning text-dark me-2">En attente</span>
            <span v-else-if="contact.statut === 'blocked'" class="badge bg-danger me-2">Bloqué</span>
            <button v-if="contact.statut !== 'blocked'" class="btn btn-outline-danger btn-sm" @click="removeContact(contact)">
              <i class="bi bi-person-x"></i>
            </button>
          </div>
        </li>
      </ul>
    </div>

    <!-- Modal d'ajout de contact -->
    <div v-if="showAddModal" class="modal-backdrop-custom">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content p-3">
          <div class="modal-header">
            <h5 class="modal-title">Ajouter un contact</h5>
            <button type="button" class="btn-close" @click="showAddModal = false"></button>
          </div>
          <div class="modal-body">
            <input v-model="addEmail" type="email" class="form-control mb-2" placeholder="Email du contact" />
            <input v-model="addPseudo" type="text" class="form-control mb-2" placeholder="Pseudo (optionnel)" />
            <div v-if="addError" class="alert alert-danger small">{{ addError }}</div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-secondary" @click="showAddModal = false">Annuler</button>
            <button class="btn btn-primary" @click="addContact" :disabled="adding">
              <span v-if="adding" class="spinner-border spinner-border-sm"></span>
              <span v-else>Ajouter</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const contacts = ref([])
const search = ref('')
const loading = ref(true)
const showAddModal = ref(false)
const addEmail = ref('')
const addPseudo = ref('')
const addError = ref('')
const adding = ref(false)

const filteredContacts = computed(() =>
  contacts.value.filter(c =>
    c.pseudo.toLowerCase().includes(search.value.toLowerCase()) ||
    c.email.toLowerCase().includes(search.value.toLowerCase())
  )
)

async function fetchContacts() {
  loading.value = true
  try {
    const res = await axios.get('http://localhost:5000/api/contacts', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    contacts.value = res.data.contacts || []
  } catch {
    contacts.value = []
  } finally {
    loading.value = false
  }
}

async function removeContact(contact) {
  if (!confirm(`Supprimer ${contact.pseudo} ?`)) return
  loading.value = true
  try {
    await axios.delete(`http://localhost:5000/api/contacts/${contact.id}`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    await fetchContacts()
  } catch (e) {
    // Afficher l’erreur si besoin
  } finally {
    loading.value = false
  }
}

async function addContact() {
  addError.value = ''
  if (!addEmail.value) {
    addError.value = "L'email est requis."
    return
  }
  adding.value = true
  try {
    await axios.post('http://localhost:5000/api/contacts', {
      email: addEmail.value,
      pseudo: addPseudo.value,
    }, {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` }
    })
    showAddModal.value = false
    addEmail.value = ''
    addPseudo.value = ''
    await fetchContacts()
  } catch (e) {
    addError.value = e.response?.data?.error || 'Erreur lors de l’ajout'
  } finally {
    adding.value = false
  }
}

function refresh() {
  fetchContacts()
}

onMounted(fetchContacts)
</script>

<style scoped>
.contacts-container {
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
.badge {
  font-size: 0.97em;
}

.modal-backdrop-custom {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(30,40,100,0.13);
  z-index: 1050;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  border-radius: 18px;
  box-shadow: 0 4px 24px #2157d344;
  min-width: 350px;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.4rem;
}
</style>
