<template>
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
                  v-model.trim="localAddEmail"
                  type="email"
                  class="form-control"
                  placeholder="nom@entreprise.com"
                  autocomplete="off"
                  autocapitalize="none"
                  spellcheck="false"
                />
              </div>
              <div v-if="localAddEmail && !emailIsValid" class="text-danger small mb-2">
                Format d'adresse invalide.
              </div>
              <div v-else-if="localAddEmail && emailExists" class="text-warning small mb-2">
                Ce contact est déjà dans votre liste.
              </div>

              <label class="form-label small text-muted">Alias (optionnel)</label>
              <div class="input-group mb-3">
                <span class="input-group-text"><i class="bi bi-person-badge"></i></span>
                <input
                  v-model.trim="localAddAlias"
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
              <div class="stats-bubble" v-if="contacts && contacts.length">
                <i class="bi bi-people-fill me-2"></i>
                Vous avez déjà {{ counts?.total ?? contacts.length }} contact{{ (counts?.total ?? contacts.length) > 1 ? 's' : '' }} actif{{ (counts?.total ?? contacts.length) > 1 ? 's' : '' }}.
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
</template>

<script setup>
import { computed, ref, watch, defineProps, defineEmits, nextTick } from 'vue'

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

// on garde les mêmes champs que dans le parent
const localAddEmail = ref(props.addEmail)
const localAddAlias = ref(props.addAlias)

// synchronisation parent -> modal
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

// validation identique à ton composant
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const emailIsValid = computed(() => emailRegex.test(localAddEmail.value))
const emailExists = computed(() =>
  props.contacts.some((c) => c.email.toLowerCase() === localAddEmail.value.toLowerCase()),
)

// fonctions avec les mêmes noms qu’avant
function closeAddModal() {
  if (props.submitting) return
  emit('close-add-modal')
}

function submitAdd() {
  // on renvoie les valeurs au parent avant de lui dire de soumettre
  emit('update:add-email', localAddEmail.value)
  emit('update:add-alias', localAddAlias.value)
  emit('submit-add')
}

function focusEmail() {
  nextTick(() => {
    addEmailInput.value?.focus()
  })
}

// on expose le focus pour que le parent fasse comme avant
defineExpose({
  focusEmail,
})
</script>

<style scoped src="@/assets/styles/contacts.css"></style>
