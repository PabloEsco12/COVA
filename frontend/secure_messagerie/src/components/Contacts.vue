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
        <input v-model="search" type="text" class="form-control" placeholder="Rechercher un contact..." />
        <button class="btn btn-outline-success" @click="openAddModal">
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
          :key="contact.id_contact"
          class="list-group-item d-flex align-items-center justify-content-between"
        >
          <div class="d-flex align-items-center">
            <template v-if="contact.avatar_url">
              <img :src="contact.avatar_url" alt="Avatar" class="avatar-sm me-2" />
            </template>
            <template v-else>
              <div class="avatar-sm-placeholder me-2">{{ initials(contact.pseudo) }}</div>
            </template>
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

    <!-- Modal d'ajout de contact (style app de messagerie) -->
    <transition name="fade">
      <div v-if="showAddModal" class="fancy-overlay" @click.self="closeAddModal">
        <div class="fancy-modal">
          <div class="fancy-header">
            <div class="d-flex align-items-center">
              <i class="bi bi-person-plus-fill text-primary me-2"></i>
              <h5 class="mb-0">Ajouter un contact</h5>
            </div>
            <button class="btn btn-sm btn-light" @click="closeAddModal" aria-label="Fermer">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
          <div class="fancy-body">
            <label class="form-label small text-muted">Email du contact</label>
            <div class="input-group mb-2 has-icon">
              <span class="input-group-text"><i class="bi bi-envelope"></i></span>
              <input
                ref="addEmailInput"
                v-model.trim="addEmail"
                type="email"
                class="form-control"
                placeholder="nom@domaine.com"
                @keyup.enter="trySubmit"
                @input="triggerSuggest(addEmail)"
              />
              <span class="input-group-text" v-if="addEmail && emailValid && !duplicate"><i class="bi bi-check-circle text-success"></i></span>
              <span class="input-group-text" v-else-if="addEmail && (!emailValid || duplicate)"><i class="bi bi-exclamation-triangle text-warning"></i></span>
            </div>
            <div class="small text-danger mb-2" v-if="addEmail && !emailValid">Format d'email invalide.</div>
            <div class="small text-warning mb-2" v-if="duplicate">Ce contact est déjà dans ta liste.</div>

            <label class="form-label small text-muted">Pseudo (optionnel)</label>
            <div class="input-group mb-2 has-icon">
              <span class="input-group-text"><i class="bi bi-person"></i></span>
              <input v-model.trim="addPseudo" type="text" class="form-control" placeholder="Ex. Marie" @keyup.enter="trySubmit" @input="triggerSuggest(addPseudo)" />
            </div>
            <div v-if="suggestions.length" class="suggest-box">
              <div class="suggest-item" v-for="u in suggestions" :key="u.id_user" @click="pickSuggestion(u)">
                <img v-if="u.avatar_url" :src="u.avatar_url" class="avatar-suggest me-2" alt="av" />
                <div v-else class="avatar-suggest-placeholder me-2">{{ initials(u.pseudo) }}</div>
                <div class="flex-grow-1 overflow-hidden">
                  <div class="fw-semibold text-truncate">{{ u.pseudo }}</div>
                  <div class="text-muted small text-truncate">{{ u.email }}</div>
                </div>
                <span v-if="contacts.some(c => c.user_id === u.id_user)" class="badge bg-secondary ms-2">Déjà contact</span>
              </div>
            </div>
            <div v-if="addError" class="alert alert-danger py-2 px-3 small mb-0">{{ addError }}</div>
          </div>
          <div class="fancy-footer">
            <button class="btn btn-light" @click="closeAddModal" :disabled="adding">Annuler</button>
            <button class="btn btn-primary" @click="addContact" :disabled="!emailValid || duplicate || adding">
              <span v-if="adding" class="spinner-border spinner-border-sm me-1"></span>
              Ajouter
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { api } from '@/utils/api'

const contacts = ref([])
const search = ref('')
const loading = ref(true)
const showAddModal = ref(false)
const addEmail = ref('')
const addPseudo = ref('')
const addError = ref('')
const adding = ref(false)
const addEmailInput = ref(null)
const suggestions = ref([])
let suggestTimer = null

const route = useRoute()
const router = useRouter()

const filteredContacts = computed(() =>
  contacts.value.filter(c =>
    (c.pseudo || '').toLowerCase().includes((search.value || '').toLowerCase()) ||
    (c.email || '').toLowerCase().includes((search.value || '').toLowerCase())
  )
)

const emailValid = computed(() => /.+@.+\..+/.test((addEmail.value || '').trim()))
const duplicate = computed(() =>
  contacts.value.some(c => (c.email || '').toLowerCase() === (addEmail.value || '').toLowerCase())
)

async function fetchContacts() {
  loading.value = true
  try {
    const res = await api.get(`/contacts`)
    contacts.value = res.data.contacts || []
  } catch {
    contacts.value = []
  } finally {
    loading.value = false
  }
}

async function removeContact(contact) {
  if (!confirm(`Supprimer ${contact.pseudo} ?`)) return
  loading.value = true
  try {
    await api.delete(`/contacts/${contact.id_contact}`)
    await fetchContacts()
  } catch (e) {
    // noop
  } finally {
    loading.value = false
  }
}

async function addContact() {
  addError.value = ''
  if (!addEmail.value) { addError.value = "L'email est requis."; return }
  if (!emailValid.value) { addError.value = "Format d'email invalide."; return }
  if (duplicate.value) { addError.value = "Ce contact existe déjà."; return }

  adding.value = true
  try {
    await api.post(`/contacts`, {
      email: addEmail.value,
      pseudo: addPseudo.value,
    })
    closeAddModal()
    addEmail.value = ''
    addPseudo.value = ''
    await fetchContacts()
  } catch (e) {
    addError.value = e.response?.data?.error || "Erreur lors de l'ajout"
  } finally {
    adding.value = false
  }
}

function refresh() { fetchContacts() }
function openAddModal() {
  addError.value = ''
  if (!showAddModal.value) {
    showAddModal.value = true
  }
  if (route.query.add !== '1') {
    router.replace({ query: { ...route.query, add: '1' } }).catch(() => {})
  }
}
function closeAddModal() {
  showAddModal.value = false
  if (route.query.add !== undefined) {
    const newQuery = { ...route.query }
    delete newQuery.add
    router.replace({ query: newQuery }).catch(() => {})
  }
}
function trySubmit() { if (emailValid.value && !duplicate.value && !adding.value) addContact() }

watch(showAddModal, async (open) => {
  if (open) {
    await nextTick(); addEmailInput.value?.focus()
    suggestions.value = []
  }
})

watch(
  () => route.query.add,
  (val) => {
    const shouldOpen = val !== undefined
    if (shouldOpen && !showAddModal.value) {
      addError.value = ''
      showAddModal.value = true
    } else if (!shouldOpen && showAddModal.value) {
      showAddModal.value = false
    }
  },
  { immediate: true }
)

onMounted(() => {
  fetchContacts()
  const handler = (e) => { if (e.key === 'Escape') closeAddModal() }
  window.addEventListener('keydown', handler)
})

function initials(name) {
  const n = (name || '').trim()
  if (!n) return 'C'
  const parts = n.split(/\s+/)
  const s = (parts[0]?.[0] || '') + (parts[1]?.[0] || '')
  return s.toUpperCase() || n[0].toUpperCase()
}

function triggerSuggest(modelRef) {
  const q = (modelRef.value || '').trim()
  if (suggestTimer) clearTimeout(suggestTimer)
  suggestTimer = setTimeout(() => searchUsers(q), 180)
}

async function searchUsers(q) {
  if (!q || q.length < 2) { suggestions.value = []; return }
  try {
    const res = await api.get(`/users/search`, { params: { q, limit: 8 } })
    suggestions.value = res.data || []
  } catch { suggestions.value = [] }
}

function pickSuggestion(u) {
  addEmail.value = u.email || ''
  addPseudo.value = u.pseudo || ''
  suggestions.value = []
}
</script>

<style scoped src="../styles/components/Contacts.css"></style>
