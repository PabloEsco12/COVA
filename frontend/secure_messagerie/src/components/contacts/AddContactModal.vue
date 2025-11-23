<template>
  <transition name="fade">
    <div v-if="showAddModal" class="modal-overlay" @click.self="closeAddModal">
      <div class="modal-card">
        <div class="modal-header">
          <div>
            <h5 class="mb-0">Ajouter un contact</h5>
            <small class="text-muted">Invitez un membre de votre organisation</small>
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
                  v-model.trim="localAddEmail"
                  type="email"
                  class="form-control"
                  placeholder="nom@entreprise.com"
                  autocomplete="off"
                  autocapitalize="none"
                  spellcheck="false"
                  @input="onEmailInput"
                  @keyup.enter.prevent="submitAdd"
                />
              </div>
              <div v-if="localAddEmail && !emailIsValid" class="text-danger small mb-2">
                Format d'adresse invalide.
              </div>
              <div v-else-if="localAddEmail && emailExists" class="text-warning small mb-2">
                Ce contact est deja dans votre liste.
              </div>
              <div v-else-if="localAddEmail && !hasSelectedSuggestion" class="text-warning small mb-2">
                Choisissez un membre de votre organisation dans la liste de suggestion.
              </div>

              <div class="suggestions" v-if="suggestionsVisible">
                <div class="d-flex justify-content-between align-items-center mb-1">
                  <span class="text-muted small">Membres de l'organisation</span>
                  <span v-if="suggestionLoading" class="spinner-border spinner-border-sm text-muted"></span>
                </div>
                <ul class="list-group">
                  <li
                    v-for="item in suggestions"
                    :key="item.user_id"
                    class="list-group-item list-group-item-action"
                    :class="{ active: item.email === localAddEmail.toLowerCase() }"
                    role="button"
                    @click="selectSuggestion(item)"
                  >
                    <div class="fw-semibold">{{ item.display_name || item.email }}</div>
                    <div class="text-muted small">
                      {{ item.email }}
                      <span class="badge bg-light text-dark ms-2">{{ roleLabel(item.role) }}</span>
                    </div>
                  </li>
                  <li v-if="!suggestionLoading && !suggestions.length" class="list-group-item text-muted small">
                    Aucun membre trouve pour "{{ localAddEmail }}".
                  </li>
                </ul>
              </div>

              <label class="form-label small text-muted">Alias (optionnel)</label>
              <div class="input-group mb-3">
                <span class="input-group-text"><i class="bi bi-person-badge"></i></span>
                <input
                  v-model.trim="localAddAlias"
                  type="text"
                  maxlength="160"
                  class="form-control"
                  placeholder="Nom personnalise"
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
                <li>Seuls les membres de l'organisation peuvent etre invites.</li>
                <li>Ajoutez un alias pour identifier rapidement ce contact dans vos conversations.</li>
                <li>Le destinataire recevra une notification securisee des que vous enregistrez la demande.</li>
              </ul>
              <div class="stats-bubble" v-if="contacts && contacts.length">
                <i class="bi bi-people-fill me-2"></i>
                Vous avez deja {{ counts?.total ?? contacts.length }} contact{{ (counts?.total ?? contacts.length) > 1 ? 's' : '' }} actif{{ (counts?.total ?? contacts.length) > 1 ? 's' : '' }}.
              </div>
            </aside>
          </div>
        </div>

        <div class="modal-footer">
          <div class="modal-hint">
            <i class="bi bi-shield-lock me-1"></i>
            Invitation chiffree : validation requise par les deux parties.
          </div>
          <div class="d-flex gap-2">
            <button class="btn btn-outline-secondary" @click="closeAddModal" :disabled="submitting">
              Annuler
            </button>
            <button
              class="btn btn-primary"
              @click="submitAdd"
              :disabled="submitting || !emailIsValid || emailExists || !hasSelectedSuggestion"
            >
              <span v-if="submitting" class="spinner-border spinner-border-sm me-1"></span>
              Ajouter
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { computed, ref, watch, defineProps, defineEmits, nextTick } from 'vue'
import { suggestOrganizationMembers } from '@/services/organization'

const props = defineProps({
  showAddModal: {
    type: Boolean,
    default: false,
  },
  addEmail: {
    type: String,
    default: '',
  },
  addAlias: {
    type: String,
    default: '',
  },
  submitting: {
    type: Boolean,
    default: false,
  },
  modalError: {
    type: String,
    default: '',
  },
  modalSuccess: {
    type: String,
    default: '',
  },
  contacts: {
    type: Array,
    default: () => [],
  },
  counts: {
    type: Object,
    default: () => null,
  },
})

const emit = defineEmits(['close-add-modal', 'submit-add', 'update:add-email', 'update:add-alias'])

const addEmailInput = ref(null)

const localAddEmail = ref(props.addEmail)
const localAddAlias = ref(props.addAlias)

watch(
  () => props.addEmail,
  (val) => {
    localAddEmail.value = val
  },
)
watch(
  () => props.addAlias,
  (val) => {
    localAddAlias.value = val
  },
)
watch(
  () => props.showAddModal,
  (open) => {
    if (!open) {
      suggestions.value = []
      selectedSuggestion.value = null
    }
  },
)

const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const emailIsValid = computed(() => emailRegex.test(localAddEmail.value))
const emailExists = computed(() =>
  props.contacts.some((c) => c.email.toLowerCase() === localAddEmail.value.toLowerCase()),
)

const selectedSuggestion = ref(null)
const suggestions = ref([])
const suggestionLoading = ref(false)
const suggestionsVisible = computed(() => !!localAddEmail.value.trim())
const hasSelectedSuggestion = computed(
  () =>
    !!selectedSuggestion.value &&
    selectedSuggestion.value.email.toLowerCase() === localAddEmail.value.toLowerCase(),
)

function closeAddModal() {
  if (props.submitting) return
  emit('close-add-modal')
}

function submitAdd() {
  emit('update:add-email', localAddEmail.value)
  emit('update:add-alias', localAddAlias.value)
  emit('submit-add')
}

function focusEmail() {
  nextTick(() => {
    addEmailInput.value?.focus()
  })
}

function roleLabel(role) {
  if (role === 'owner') return 'Proprietaire'
  if (role === 'admin') return 'Admin'
  return 'Membre'
}

let debounceTimer = null
async function fetchSuggestions() {
  if (!localAddEmail.value.trim()) {
    suggestions.value = []
    selectedSuggestion.value = null
    return
  }
  suggestionLoading.value = true
  try {
    const data = await suggestOrganizationMembers(localAddEmail.value, 10)
    suggestions.value = Array.isArray(data) ? data : []
  } catch (err) {
    suggestions.value = []
  } finally {
    suggestionLoading.value = false
  }
}

function onEmailInput() {
  selectedSuggestion.value = null
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchSuggestions, 250)
}

function selectSuggestion(item) {
  selectedSuggestion.value = item
  localAddEmail.value = item.email
  emit('update:add-email', localAddEmail.value)
}

defineExpose({
  focusEmail,
})
</script>

<style scoped src="@/assets/styles/contacts.css"></style>
