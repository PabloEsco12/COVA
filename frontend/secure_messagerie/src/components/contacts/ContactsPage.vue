<template>
  <div class="contacts-page">
    <!-- Header -->
    <div class="contacts-header">
      <div>
        <h2 class="title"><i class="bi bi-people-fill me-2"></i>Contacts</h2>
        <p class="subtitle">Gérez votre réseau sécurisé et gardez le contrôle sur vos échanges.</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline-secondary" @click="refresh" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-1"></span>
          <i v-else class="bi bi-arrow-clockwise me-1"></i>
          Rafraîchir
        </button>
        <button class="btn btn-primary ms-2" @click="openAddModal">
          <i class="bi bi-person-plus-fill me-1"></i>
          Nouveau contact
        </button>
      </div>
    </div>

    <!-- Toolbar -->
    <ContactsToolbar
      class="mb-3"
      :search-term="searchTerm"
      :status-filter="statusFilter"
      :filter-chips="filterChips"
      @update:search-term="searchTerm = $event"
      @update:status-filter="statusFilter = $event"
    />

    <!-- Feedback -->
    <div
      v-if="feedback.message"
      class="alert"
      :class="feedback.type === 'error' ? 'alert-danger' : 'alert-success'"
    >
      {{ feedback.message }}
    </div>
    <div v-if="loadError" class="alert alert-danger">
      {{ loadError }}
    </div>

    <!-- Skeleton -->
    <div v-if="loading" class="skeleton-list">
      <div v-for="n in 4" :key="`sk-${n}`" class="skeleton-card">
        <div class="skeleton-avatar"></div>
        <div class="skeleton-lines">
          <div class="line w-60"></div>
          <div class="line w-40"></div>
        </div>
      </div>
    </div>

    <!-- Contenu -->
    <template v-else>
      <!-- état vide -->
      <div v-if="!hasVisibleContacts" class="empty-state card">
        <div class="empty-icon">
          <i class="bi bi-people"></i>
        </div>
        <h4>Pas de contact à afficher</h4>
        <p class="text-muted">
          Ajoutez vos collègues ou partenaires COVA pour échanger en toute sécurité.
        </p>
        <button class="btn btn-primary" @click="openAddModal">
          <i class="bi bi-person-plus me-1"></i>
          Ajouter un premier contact
        </button>
      </div>

      <!-- sections -->
      <template v-else>
        <ContactSection
          v-for="section in sectionsToDisplay"
          :key="section.key"
          :section="section"
        >
          <template #default="{ contact }">
            <ContactCard
              :contact="contact"
              :highlight="contact.id === highlightContactId"
              :busy="isBusy(contact.id)"
              :editing-alias="editingAliasFor === contact.id"
              :alias-draft="aliasDraft"
              :alias-saving="aliasSaving && editingAliasFor === contact.id"
              @open-details="openDetails"
              @start-alias-edit="startAliasEdit"
              @cancel-alias-edit="cancelAliasEdit"
              @save-alias="onSaveAlias"
              @set-status="onSetStatus"
              @prompt-delete="promptDelete"
              @open-conversation="openConversation"
              @set-alias-input-ref="(el) => setAliasInputRef(contact.id, el)"
            />
          </template>
        </ContactSection>
      </template>
    </template>

    <!-- Modale ajout -->
    <AddContactModal
      :show-add-modal="showAddModal"
      :add-email="addEmail"
      :add-alias="addAlias"
      :submitting="submitting"
      :modal-error="modalError"
      :modal-success="modalSuccess"
      :contacts="contacts"
      :counts="counts"
      ref="addContactModalRef"
      @close-add-modal="closeAddModal"
      @submit-add="submitAdd"
      @update:add-email="addEmail = $event"
      @update:add-alias="addAlias = $event"
    />

    <!-- Modale suppression -->
    <DeleteContactModal
      :show-delete-modal="showDeleteModal"
      :delete-target="deleteTarget"
      :delete-busy="deleteBusy"
      :delete-error="deleteError"
      @close-delete-modal="closeDeleteModal"
      @confirm-delete="confirmDelete"
    />

    <!-- Modale détails -->
    <ContactDetailsModal
      :detail-contact="detailContact"
      v-if="detailContact"
      @close-details-modal="closeDetailsModal"
      @open-conversation="openConversation"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { backendBase } from '@/utils/api'
import { normalizeAvatarUrl } from '@/utils/profile'

import ContactsToolbar from './ContactsToolbar.vue'
import ContactSection from './ContactSection.vue'
import ContactCard from './ContactCard.vue'
import AddContactModal from './AddContactModal.vue'
import DeleteContactModal from './DeleteContactModal.vue'
import ContactDetailsModal from './ContactDetailsModal.vue'

import {
  createContact,
  deleteContact,
  fetchContacts,
  updateContactAlias,
  updateContactStatus,
} from '@/services/contacts'

const contacts = ref([])
const loading = ref(true)
const loadError = ref('')

const searchTerm = ref('')
const statusFilter = ref('all')

const feedback = reactive({ type: 'success', message: '' })

// ajout
const showAddModal = ref(false)
const addEmail = ref('')
const addAlias = ref('')
const submitting = ref(false)
const modalError = ref('')
const modalSuccess = ref('')
const addContactModalRef = ref(null)

// suppression
const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const deleteBusy = ref(false)
const deleteError = ref('')

// détails
const detailContact = ref(null)

// alias
const editingAliasFor = ref(null)
const aliasDraft = ref('')
const aliasSaving = ref(false)
const aliasInputRefs = new Map()

// divers
const highlightContactId = ref(null)
const busyMap = reactive({})

const router = useRouter()

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const normalizedEmail = computed(() => (addEmail.value || '').trim())
const normalizedEmailLower = computed(() => normalizedEmail.value.toLowerCase())
const emailIsValid = computed(() => emailRegex.test(normalizedEmail.value))
const existingContact = computed(() => {
  const target = normalizedEmailLower.value
  if (!target) return null
  return contacts.value.find((c) => (c.email || '').toLowerCase() === target) || null
})
const emailExists = computed(() => !!existingContact.value)

const statusOrder = {
  accepted: 0,
  pending: 1,
  blocked: 2,
}

const counts = computed(() => ({
  accepted: contacts.value.filter((c) => c.status === 'accepted').length,
  pending: contacts.value.filter((c) => c.status === 'pending').length,
  blocked: contacts.value.filter((c) => c.status === 'blocked').length,
  total: contacts.value.length,
}))

function emitPendingContactCount(value) {
  if (typeof window === 'undefined') return
  const normalized = Math.max(0, Number(value) || 0)
  window.dispatchEvent(
    new CustomEvent('cova:contacts-pending', {
      detail: { pending: normalized },
    }),
  )
}

watch(
  () => counts.value.pending,
  (value) => {
    emitPendingContactCount(value)
  },
  { immediate: true },
)

const filterChips = computed(() => [
  { value: 'all', label: 'Tous', count: counts.value.total },
  { value: 'accepted', label: 'Actifs', count: counts.value.accepted },
  { value: 'pending', label: 'En attente', count: counts.value.pending },
  { value: 'blocked', label: 'Bloqués', count: counts.value.blocked },
])

const normalizedContacts = computed(() => {
  return contacts.value
    .map((contact) => ({
      ...contact,
      avatar_url: normalizeAvatarUrl(contact.avatar_url || null, { baseUrl: backendBase }),
    }))
    .sort((a, b) => {
      const statusDiff = statusOrder[a.status] - statusOrder[b.status]
      if (statusDiff !== 0) return statusDiff
      return displayName(a).localeCompare(displayName(b))
    })
})

const searchLower = computed(() => searchTerm.value.trim().toLowerCase())

const filteredContacts = computed(() => {
  const lookup = searchLower.value
  if (!lookup) return normalizedContacts.value
  return normalizedContacts.value.filter((contact) => {
    const haystack = [
      contact.email,
      contact.display_name,
      contact.alias,
      displayName(contact),
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return haystack.includes(lookup)
  })
})

const groupedContacts = computed(() => ({
  accepted: filteredContacts.value.filter((c) => c.status === 'accepted'),
  pending: filteredContacts.value.filter((c) => c.status === 'pending'),
  blocked: filteredContacts.value.filter((c) => c.status === 'blocked'),
}))

const sectionsToDisplay = computed(() => {
  if (statusFilter.value === 'all') {
    return [
      {
        key: 'pending',
        title: 'Demandes en attente',
        description:
          "Validez ou refusez les demandes de connexion. Les deux parties doivent confirmer pour ouvrir la discussion.",
        contacts: groupedContacts.value.pending,
      },
      {
        key: 'accepted',
        title: 'Contacts actifs',
        description: 'Contacts approuvés avec lesquels vous pouvez échanger immédiatement.',
        contacts: groupedContacts.value.accepted,
      },
      {
        key: 'blocked',
        title: 'Contacts bloqués',
        description: null,
        contacts: groupedContacts.value.blocked,
      },
    ]
  }
  return [
    {
      key: statusFilter.value,
      title:
        statusFilter.value === 'pending'
          ? 'Demandes en attente'
          : statusFilter.value === 'blocked'
            ? 'Contacts bloqués'
            : 'Contacts actifs',
      description: null,
      contacts: groupedContacts.value[statusFilter.value],
    },
  ]
})

const hasVisibleContacts = computed(() =>
  sectionsToDisplay.value.some((section) => section.contacts.length > 0),
)

function displayName(contact) {
  return (
    (contact.alias && contact.alias.trim()) ||
    (contact.display_name && contact.display_name.trim()) ||
    contact.email.split('@')[0]
  )
}

function secondaryLabel(contact) {
  if (contact.job_title) {
    return contact.job_title
  }
  if (contact.department) {
    return contact.department
  }
  if (contact.alias && contact.display_name && contact.alias !== contact.display_name) {
    return contact.display_name
  }
  return contact.email
}

function initials(contact) {
  const label = displayName(contact)
  const parts = label.split(/\\s+/).filter(Boolean)
  const letters = parts.slice(0, 2).map((word) => word[0])
  return letters.join('').toUpperCase() || label.slice(0, 2).toUpperCase()
}

function statusLabel(status) {
  switch (status) {
    case 'accepted':
      return 'Contact actif'
    case 'pending':
      return 'En attente'
    case 'blocked':
      return 'Bloqué'
    default:
      return status
  }
}

function formatDate(value) {
  try {
    return new Date(value).toLocaleDateString()
  } catch {
    return ''
  }
}

function setFeedback(type, message) {
  feedback.type = type
  feedback.message = message
  if (message) {
    setTimeout(() => {
      if (feedback.message === message) {
        feedback.message = ''
      }
    }, 3500)
  }
}

function isBusy(contactId) {
  return !!busyMap[contactId]
}

function setBusy(contactId, value) {
  busyMap[contactId] = value
}

async function loadContacts() {
  loading.value = true
  loadError.value = ''
  try {
    const data = await fetchContacts()
    contacts.value = Array.isArray(data) ? data : []
  } catch (error) {
    loadError.value = error?.response?.data?.detail || 'Impossible de charger les contacts.'
  } finally {
    loading.value = false
  }
}

async function refresh() {
  await loadContacts()
  setFeedback('success', 'Liste des contacts mise à jour.')
}

function openAddModal() {
  showAddModal.value = true
  addEmail.value = ''
  addAlias.value = ''
  modalError.value = ''
  modalSuccess.value = ''
  nextTick(() => {
    // on utilise le composant enfant pour focus comme avant
    addContactModalRef.value?.focusEmail?.()
  })
}

function closeAddModal() {
  if (submitting.value) return
  showAddModal.value = false
}

async function submitAdd() {
  modalError.value = ''
  modalSuccess.value = ''
  if (!emailIsValid.value) {
    modalError.value = 'Veuillez saisir une adresse e-mail valide.'
    return
  }
  const duplicate = existingContact.value
  if (duplicate) {
    if (duplicate.status === 'pending') {
      if (duplicate.awaiting_my_response) {
        modalError.value = 'Ce contact attend votre réponse dans les demandes en attente.'
      } else {
        modalSuccess.value = "Demande envoyée : le contact sera visible après confirmation."
      }
    } else if (duplicate.status === 'accepted') {
      modalError.value = 'Ce contact figure déjà dans votre liste.'
    } else {
      modalError.value = 'Ce contact est déjà en cours de traitement.'
    }
    highlightContactId.value = duplicate.id
    setTimeout(() => {
      highlightContactId.value = null
    }, 3000)
    return
  }
  submitting.value = true
  const targetEmail = normalizedEmail.value
  try {
    const contact = await createContact({
      email: targetEmail,
      alias: addAlias.value || null,
    })
    contacts.value.push(contact)
    modalSuccess.value = "Demande envoyée : le contact sera visible après confirmation."
    highlightContactId.value = contact.id
    setFeedback('success', 'Contact ajouté. En attente de confirmation.')
    setTimeout(() => {
      highlightContactId.value = null
    }, 4000)
  } catch (error) {
    if (error?.response?.status === 404) {
      modalError.value = 'Aucun utilisateur trouvé avec cette adresse e-mail.'
    } else if (error?.response?.status === 409) {
      modalSuccess.value = "Demande envoyée : le contact sera visible après confirmation."
    } else {
      modalError.value =
        error?.response?.data?.detail || "Impossible d'ajouter ce contact pour le moment."
    }
  } finally {
    submitting.value = false
  }
}

function startAliasEdit(contact) {
  editingAliasFor.value = contact.id
  aliasDraft.value = contact.alias || ''
  aliasSaving.value = false
  nextTick(() => {
    const input = aliasInputRefs.get(contact.id)
    input?.focus()
  })
}

function cancelAliasEdit() {
  if (aliasSaving.value) return
  editingAliasFor.value = null
  aliasDraft.value = ''
}

async function saveAlias(contact) {
  aliasSaving.value = true
  try {
    const updated = await updateContactAlias(contact.id, aliasDraft.value || null)
    Object.assign(contact, updated)
    setFeedback('success', 'Alias mis à jour.')
    cancelAliasEdit()
  } catch (error) {
    setFeedback(
      'error',
      error?.response?.data?.detail || "Impossible de mettre à jour l'alias pour le moment.",
    )
  } finally {
    aliasSaving.value = false
  }
}

function onSaveAlias(payload) {
  // payload = { contact, value }
  // on garde le comportement d’origine (le parent possède aliasDraft)
  aliasDraft.value = payload.value
  saveAlias(payload.contact)
}

async function setStatus(contact, status) {
  setBusy(contact.id, true)
  try {
    const updated = await updateContactStatus(contact.id, status)
    Object.assign(contact, updated)
    setFeedback(
      'success',
      status === 'accepted'
        ? 'Contact accepté.'
        : status === 'blocked'
          ? 'Contact bloqué.'
          : 'Statut mis à jour.',
    )
  } catch (error) {
    setFeedback(
      'error',
      error?.response?.data?.detail || 'Impossible de mettre à jour le statut.',
    )
  } finally {
    setBusy(contact.id, false)
  }
}

function onSetStatus(payload) {
  // payload = { contact, status }
  setStatus(payload.contact, payload.status)
}

function promptDelete(contact) {
  deleteTarget.value = contact
  deleteError.value = ''
  showDeleteModal.value = true
}

function openDetails(contact) {
  detailContact.value = contact
}

function closeDetailsModal() {
  detailContact.value = null
}

function closeDeleteModal() {
  if (deleteBusy.value) return
  showDeleteModal.value = false
  deleteTarget.value = null
  deleteError.value = ''
}

async function confirmDelete() {
  if (!deleteTarget.value) return
  const contact = deleteTarget.value
  deleteBusy.value = true
  setBusy(contact.id, true)
  try {
    await deleteContact(contact.id)
    contacts.value = contacts.value.filter((c) => c.id !== contact.id)
    if (detailContact.value?.id === contact.id) {
      detailContact.value = null
    }
    setFeedback('success', 'Contact supprimé.')
    closeDeleteModal()
  } catch (error) {
    deleteError.value =
      error?.response?.data?.detail || 'Impossible de supprimer ce contact pour le moment.'
    setFeedback('error', deleteError.value)
  } finally {
    deleteBusy.value = false
    setBusy(contact.id, false)
  }
}

function openConversation(contact) {
  detailContact.value = null
  router.push({
    path: '/dashboard/messages',
    query: { contact: contact.contact_user_id },
  })
}

function setAliasInputRef(id, el) {
  if (el) {
    aliasInputRefs.set(id, el)
  } else {
    aliasInputRefs.delete(id)
  }
}

onMounted(async () => {
  await loadContacts()
})
</script>

<style scoped src="@/assets/styles/contacts.css"></style>

