<template>
  <div class="contacts-page">
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

    <div class="toolbar card mb-3">
      <div class="search-group">
        <i class="bi bi-search text-muted"></i>
        <input
          v-model.trim="searchTerm"
          type="search"
          class="form-control border-0"
          placeholder="Rechercher par nom, alias ou adresse e-mail"
        />
      </div>
      <div class="filter-group">
        <button
          v-for="chip in filterChips"
          :key="chip.value"
          class="filter-chip"
          :class="{ active: statusFilter === chip.value }"
          @click="statusFilter = chip.value"
        >
          <span>{{ chip.label }}</span>
          <span class="badge bg-light text-secondary">{{ chip.count }}</span>
        </button>
      </div>
    </div>

    <div v-if="feedback.message" class="alert" :class="feedback.type === 'error' ? 'alert-danger' : 'alert-success'">
      {{ feedback.message }}
    </div>
    <div v-if="loadError" class="alert alert-danger">
      {{ loadError }}
    </div>

    <div v-if="loading" class="skeleton-list">
      <div v-for="n in 4" :key="`sk-${n}`" class="skeleton-card">
        <div class="skeleton-avatar"></div>
        <div class="skeleton-lines">
          <div class="line w-60"></div>
          <div class="line w-40"></div>
        </div>
      </div>
    </div>

    <template v-else>
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

      <template v-else>
        <section
          v-for="section in sectionsToDisplay"
          :key="section.key"
          v-show="section.contacts.length"
          class="contact-section"
        >
          <div class="section-heading">
            <div>
              <h5 class="mb-1">{{ section.title }}</h5>
              <p v-if="section.description" class="text-muted small mb-0">
                {{ section.description }}
              </p>
            </div>
            <span class="badge bg-secondary-subtle text-secondary-emphasis">
              {{ section.contacts.length }}
            </span>
          </div>

          <div class="contact-grid">
            <article
              v-for="contact in section.contacts"
              :key="contact.id"
              class="contact-card card"
              :class="[
                `contact-card--${contact.status}`,
                { 'contact-card--highlight': contact.id === highlightContactId },
              ]"
            >
              <div class="card-body">
                <div
                  class="contact-main contact-main--interactive"
                  role="button"
                  tabindex="0"
                  @click="openDetails(contact)"
                  @keydown.enter.prevent="openDetails(contact)"
                  @keydown.space.prevent="openDetails(contact)"
                >
                  <div class="contact-avatar">
                    <img v-if="contact.avatar_url" :src="contact.avatar_url" alt="avatar" />
                    <span v-else>{{ initials(contact) }}</span>
                  </div>
                  <div class="contact-info">
                    <div class="contact-name">
                      <strong>{{ displayName(contact) }}</strong>
                      <button
                        v-if="contact.status === 'accepted'"
                        class="btn btn-link btn-sm"
                        @click.stop="startAliasEdit(contact)"
                        title="Modifier l'alias"
                      >
                        <i class="bi bi-pencil-square"></i>
                      </button>
                    </div>
                    <div class="contact-meta text-muted small">
                      <span>{{ secondaryLabel(contact) }}</span>
                      <span class="dot-separator"></span>
                      <span>{{ statusLabel(contact.status) }}</span>
                      <span v-if="contact.created_at" class="d-none d-md-inline">
                        <span class="dot-separator"></span>
                        Ajouté le {{ formatDate(contact.created_at) }}
                      </span>
                    </div>
                  </div>
                </div>

                <div
                  v-if="editingAliasFor === contact.id"
                  class="alias-editor input-group input-group-sm mt-2"
                  @click.stop
                >
                  <input
                    :ref="(el) => setAliasInputRef(contact.id, el)"
                    v-model.trim="aliasDraft"
                    type="text"
                    class="form-control"
                    maxlength="160"
                    placeholder="Alias personnalisé"
                    @keyup.enter="saveAlias(contact)"
                    @keyup.esc="cancelAliasEdit"
                  />
                  <button class="btn btn-outline-secondary" @click="cancelAliasEdit">
                    Annuler
                  </button>
                  <button class="btn btn-primary" @click="saveAlias(contact)">
                    <span v-if="aliasSaving" class="spinner-border spinner-border-sm"></span>
                    <span v-else>Enregistrer</span>
                  </button>
                </div>

                <div class="contact-actions">
                  <template v-if="contact.status === 'pending'">
                    <button
                      class="btn btn-success btn-sm"
                      :disabled="isBusy(contact.id)"
                      @click="setStatus(contact, 'accepted')"
                    >
                      <span v-if="isBusy(contact.id)" class="spinner-border spinner-border-sm me-1"></span>
                      Accepter
                    </button>
                    <button
                      class="btn btn-outline-secondary btn-sm"
                      :disabled="isBusy(contact.id)"
                      @click="setStatus(contact, 'blocked')"
                    >
                      Bloquer
                    </button>
                    <button
                      class="btn btn-outline-danger btn-sm"
                      :disabled="isBusy(contact.id)"
                      @click="promptDelete(contact)"
                    >
                      Refuser
                    </button>
                  </template>

                  <template v-else-if="contact.status === 'accepted'">
                    <button
                      class="btn btn-outline-primary btn-sm"
                      @click="openConversation(contact)"
                    >
                      <i class="bi bi-chat-dots me-1"></i> Converser
                    </button>
                    <button
                      class="btn btn-outline-secondary btn-sm"
                      :disabled="isBusy(contact.id)"
                      @click="setStatus(contact, 'blocked')"
                    >
                      Bloquer
                    </button>
                    <button
                      class="btn btn-outline-danger btn-sm"
                      :disabled="isBusy(contact.id)"
                      @click="promptDelete(contact)"
                    >
                      Supprimer
                    </button>
                  </template>

                  <template v-else>
                    <button
                      class="btn btn-outline-success btn-sm"
                      :disabled="isBusy(contact.id)"
                      @click="setStatus(contact, 'accepted')"
                    >
                      Débloquer
                    </button>
                    <button
                      class="btn btn-outline-danger btn-sm"
                      :disabled="isBusy(contact.id)"
                      @click="promptDelete(contact)"
                    >
                      Supprimer
                    </button>
                  </template>
                </div>
              </div>
            </article>
          </div>
        </section>
      </template>
    </template>

    <transition name="fade">
      <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
        <div class="modal-card">
          <div class="modal-header">
            <div>
              <h5 class="mb-0">Ajouter un contact</h5>
              <small class="text-muted">Invitez une personne disposant déjà d’un compte</small>
            </div>
            <button class="btn btn-sm btn-outline-secondary" @click="closeAddModal">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>

          <div class="modal-body">
            <div class="modal-grid">
              <div>
                <label class="form-label small text-muted">Adresse e-mail</label>
                <div class="input-group mb-2">
                  <span class="input-group-text"><i class="bi bi-envelope"></i></span>
                  <input
                    ref="addEmailInput"
                    v-model.trim="addEmail"
                    type="email"
                    class="form-control"
                    placeholder="nom@entreprise.com"
                    autocomplete="off"
                    autocapitalize="none"
                    spellcheck="false"
                  />
                </div>
                <div v-if="addEmail && !emailIsValid" class="text-danger small mb-2">
                  Format d'adresse invalide.
                </div>
                <div v-else-if="addEmail && emailExists" class="text-warning small mb-2">
                  Ce contact est déjà dans votre liste.
                </div>

                <label class="form-label small text-muted">Alias (optionnel)</label>
                <div class="input-group mb-3">
                  <span class="input-group-text"><i class="bi bi-person-badge"></i></span>
                  <input
                    v-model.trim="addAlias"
                    type="text"
                    maxlength="160"
                    class="form-control"
                    placeholder="Nom personnalisé"
                  />
                </div>

                <div v-if="modalError" class="alert alert-danger py-2">
                  {{ modalError }}
                </div>
                <div v-if="modalSuccess" class="alert alert-success py-2">
                  {{ modalSuccess }}
                </div>
              </div>
              <aside class="modal-aside">
                <h6 class="aside-title">Avant d'envoyer</h6>
                <ul class="aside-list">
                  <li>Vérifiez l'adresse : seule une personne disposant d'un compte pourra accepter.</li>
                  <li>Ajoutez un alias pour identifier rapidement ce contact dans vos conversations.</li>
                  <li>Le destinataire recevra une notification sécurisée dès que vous enregistrez la demande.</li>
                </ul>
                <div class="stats-bubble" v-if="contacts.length">
                  <i class="bi bi-people-fill me-2"></i>
                  Vous avez déjà {{ counts.total }} contact{{ counts.total > 1 ? 's' : '' }} actif{{ counts.total > 1 ? 's' : '' }}.
                </div>
              </aside>
            </div>
          </div>

          <div class="modal-footer">
            <div class="modal-hint">
              <i class="bi bi-shield-lock me-1"></i>
              Invitation chiffrée : validation requise par les deux parties.
            </div>
            <div class="d-flex gap-2">
              <button class="btn btn-outline-secondary" @click="closeAddModal" :disabled="submitting">
                Annuler
              </button>
              <button
                class="btn btn-primary"
                @click="submitAdd"
                :disabled="submitting || !emailIsValid || emailExists"
              >
                <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
                Ajouter
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="showDeleteModal" class="modal-overlay" @click.self="closeDeleteModal">
        <div class="modal-card danger-card">
          <div class="modal-header">
            <div>
              <h5 class="mb-0 text-danger">
                <i class="bi bi-exclamation-triangle me-2"></i> Supprimer ce contact ?
              </h5>
              <small class="text-muted">
                Cette action retire la relation pour vous deux. Les conversations existantes ne sont pas supprimées.
              </small>
            </div>
            <button class="btn btn-sm btn-outline-secondary" @click="closeDeleteModal" :disabled="deleteBusy">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
          <div class="modal-body">
            <div v-if="deleteTarget" class="delete-preview">
              <div class="contact-avatar preview-avatar">
                <img v-if="deleteTarget.avatar_url" :src="deleteTarget.avatar_url" alt="avatar" />
                <span v-else>{{ initials(deleteTarget) }}</span>
              </div>
              <div class="flex-grow-1">
                <h6 class="mb-1">{{ displayName(deleteTarget) }}</h6>
                <p class="text-muted small mb-0">{{ deleteTarget.email }}</p>
              </div>
            </div>
            <p class="text-muted small mt-3 mb-0">
              Vous pourrez envoyer une nouvelle invitation si nécessaire. Le contact sera notifié de la suppression.
            </p>
            <div v-if="deleteError" class="alert alert-danger py-2 mt-3">
              {{ deleteError }}
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline-secondary" @click="closeDeleteModal" :disabled="deleteBusy">
              Annuler
            </button>
            <button class="btn btn-danger" @click="confirmDelete" :disabled="deleteBusy">
              <span v-if="deleteBusy" class="spinner-border spinner-border-sm me-1"></span>
              Supprimer définitivement
            </button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="detailContact" class="modal-overlay" @click.self="closeDetailsModal">
        <div class="modal-card detail-card">
          <div class="modal-header">
            <div>
              <h5 class="mb-0">
                <i class="bi bi-person-vcard me-2"></i>Fiche contact
              </h5>
              <small class="text-muted">Informations partagées depuis le profil sécurisé.</small>
            </div>
            <button class="btn btn-sm btn-outline-secondary" @click="closeDetailsModal">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
          <div class="modal-body detail-body" v-if="detailContact">
            <div class="detail-hero mb-3">
              <div class="contact-avatar detail-avatar">
                <img v-if="detailContact.avatar_url" :src="detailContact.avatar_url" alt="avatar" />
                <span v-else>{{ initials(detailContact) }}</span>
              </div>
              <div>
                <h4 class="mb-1">{{ displayName(detailContact) }}</h4>
                <p class="text-muted mb-2">{{ detailContact.email }}</p>
                <p v-if="detailContact.status_message" class="detail-status">
                  <i class="bi bi-chat-quote-fill me-2 text-primary"></i>{{ detailContact.status_message }}
                </p>
              </div>
            </div>
            <div class="detail-grid">
              <div class="detail-field">
                <span class="label">Fonction</span>
                <span class="value">{{ detailContact.job_title || 'Non renseigné' }}</span>
              </div>
              <div class="detail-field">
                <span class="label">Département / équipe</span>
                <span class="value">{{ detailContact.department || 'Non renseigné' }}</span>
              </div>
              <div class="detail-field">
                <span class="label">Téléphone sécurisé</span>
                <span class="value">{{ detailContact.phone_number || 'Non communiqué' }}</span>
              </div>
              <div class="detail-field">
                <span class="label">Statut</span>
                <span class="value">{{ statusLabel(detailContact.status) }}</span>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline-secondary" @click="closeDetailsModal">Fermer</button>
            <button class="btn btn-primary" @click="openConversation(detailContact)">
              <i class="bi bi-chat-dots me-1"></i>Ouvrir une conversation
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

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

const showAddModal = ref(false)
const addEmail = ref('')
const addAlias = ref('')
const submitting = ref(false)
const modalError = ref('')
const modalSuccess = ref('')

const showDeleteModal = ref(false)
const deleteTarget = ref(null)
const deleteBusy = ref(false)
const deleteError = ref('')
const detailContact = ref(null)

const editingAliasFor = ref(null)
const aliasDraft = ref('')
const aliasSaving = ref(false)

const addEmailInput = ref(null)
const highlightContactId = ref(null)
const busyMap = reactive({})
const aliasInputRefs = new Map()

const router = useRouter()

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const emailIsValid = computed(() => emailRegex.test(addEmail.value))
const emailExists = computed(() =>
  contacts.value.some((contact) => contact.email.toLowerCase() === addEmail.value.toLowerCase()),
)

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

const filterChips = computed(() => [
  { value: 'all', label: 'Tous', count: counts.value.total },
  { value: 'accepted', label: 'Actifs', count: counts.value.accepted },
  { value: 'pending', label: 'En attente', count: counts.value.pending },
  { value: 'blocked', label: 'Bloqués', count: counts.value.blocked },
])

const normalizedContacts = computed(() => {
  return contacts.value
    .slice()
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
  const parts = label.split(/\s+/).filter(Boolean)
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
    addEmailInput.value?.focus()
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
  if (emailExists.value) {
    modalError.value = 'Ce contact figure déjà dans votre liste.'
    return
  }
  submitting.value = true
  try {
    const contact = await createContact({
      email: addEmail.value,
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
      modalError.value = 'Le contact existe déjà.'
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

<style scoped>
.contacts-page {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.contacts-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0.5rem 0;
}

.title {
  margin: 0;
  font-weight: 600;
}

.subtitle {
  margin: 0;
  color: #6b7280;
}

.header-actions {
  display: flex;
  align-items: center;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
}

.search-group {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8fafc;
  border-radius: 0.75rem;
}

.search-group input {
  background: transparent;
  box-shadow: none;
}

.filter-group {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #334155;
  transition: all 0.2s ease;
}

.filter-chip.active {
  background: #1d4ed8;
  color: #fff;
  border-color: #1d4ed8;
}

.filter-chip .badge {
  font-size: 0.7rem;
}

.skeleton-list {
  display: grid;
  gap: 0.75rem;
}

.skeleton-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #ffffff;
  border-radius: 1rem;
  border: 1px solid #e2e8f0;
}

.skeleton-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: linear-gradient(90deg, #e2e8f0 0%, #f1f5f9 50%, #e2e8f0 100%);
  animation: shimmer 1.4s infinite;
}

.skeleton-lines {
  flex: 1;
  display: grid;
  gap: 0.35rem;
}

.line {
  height: 10px;
  border-radius: 999px;
  background: linear-gradient(90deg, #e2e8f0 0%, #f1f5f9 50%, #e2e8f0 100%);
  animation: shimmer 1.4s infinite;
}

.line.w-60 {
  width: 60%;
}

.line.w-40 {
  width: 40%;
}

@keyframes shimmer {
  0% {
    background-position: -200px 0;
  }
  100% {
    background-position: 200px 0;
  }
}

.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  border-radius: 1.25rem;
  border: 1px dashed #cbd5f5;
  background: #f8fbff;
}

.empty-icon {
  font-size: 3rem;
  color: #1d4ed8;
  margin-bottom: 1rem;
}

.contact-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0 0.25rem;
}

.contact-grid {
  display: grid;
  gap: 0.75rem;
}

.contact-card {
  border-radius: 1rem;
  border: 1px solid #e2e8f0;
  transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.contact-card:hover {
  border-color: #cbd5f5;
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
}

.contact-card--highlight {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.2);
}

.contact-card--pending {
  border-left: 4px solid #f59e0b;
}

.contact-card--accepted {
  border-left: 4px solid #22c55e;
}

.contact-card--blocked {
  border-left: 4px solid #ef4444;
}

.contact-main {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.contact-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  overflow: hidden;
  background: #1d4ed8;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  letter-spacing: 0.05em;
}

.contact-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.contact-info {
  flex: 1;
  min-width: 0;
}

.contact-name {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.contact-name button {
  padding: 0;
  font-size: 0.8rem;
}

.contact-meta {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.dot-separator::before {
  content: '•';
  color: #cbd5f5;
}

.contact-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.contact-main--interactive {
  cursor: pointer;
}

.contact-main--interactive:focus-visible {
  outline: 2px solid #2563eb;
  outline-offset: 4px;
  border-radius: 0.85rem;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  z-index: 1050;
}

.modal-card {
  width: min(620px, 100%);
  background: #fff;
  border-radius: 1rem;
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.3);
  display: flex;
  flex-direction: column;
}

.detail-card {
  width: min(640px, 100%);
}

.detail-body {
  background: #fdfdff;
}

.detail-hero {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.detail-avatar {
  width: 70px;
  height: 70px;
  font-size: 1.2rem;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
}

.detail-field {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.95rem;
  padding: 0.75rem 0.9rem;
}

.detail-field .label {
  display: block;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #94a3b8;
  margin-bottom: 0.3rem;
}

.detail-field .value {
  font-weight: 600;
  color: #0f172a;
}

.detail-status {
  background: #eef2ff;
  border-radius: 0.75rem;
  padding: 0.65rem 0.85rem;
  color: #1e3a8a;
  font-style: italic;
}

.danger-card {
  border-top: 4px solid #ef4444;
}

.modal-header,
.modal-footer {
  padding: 1rem 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-footer {
  border-top: 1px solid #e2e8f0;
  border-bottom: none;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  padding: 1rem 1.25rem;
}

.modal-grid {
  display: grid;
  gap: 1rem;
}

.modal-aside {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 0.9rem;
  padding: 1rem;
  font-size: 0.85rem;
  color: #475569;
}

.aside-title {
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #1f2a37;
}

.aside-list {
  padding-left: 1.1rem;
  margin-bottom: 0.75rem;
}

.aside-list li {
  margin-bottom: 0.35rem;
}

.stats-bubble {
  display: inline-flex;
  align-items: center;
  padding: 0.35rem 0.75rem;
  background: rgba(37, 99, 235, 0.08);
  color: #1d4ed8;
  border-radius: 999px;
  font-weight: 500;
}

.modal-hint {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.8rem;
  color: #64748b;
}

.danger-card .modal-footer {
  justify-content: flex-end;
  gap: 0.75rem;
}

.delete-preview {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 0.85rem;
  background: #fff7f7;
  border: 1px solid #fecdd3;
  border-radius: 0.85rem;
}

.preview-avatar {
  width: 52px;
  height: 52px;
  font-size: 1rem;
  background: #f97316;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .contacts-header {
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-group {
    width: 100%;
  }

  .filter-group {
    width: 100%;
  }

  .modal-grid {
    grid-template-columns: 1fr;
  }

  .modal-footer {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }

  .modal-hint {
    justify-content: center;
  }

  .contact-card {
    border-left-width: 0;
    border-top-width: 4px;
  }
}

@media (min-width: 769px) {
  .modal-grid {
    grid-template-columns: minmax(0, 1fr) minmax(0, 0.85fr);
    align-items: start;
  }

  .modal-aside {
    height: 100%;
  }
}
</style>
