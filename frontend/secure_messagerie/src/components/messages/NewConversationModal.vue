<!--
  ===== Component Header =====
  Component: NewConversationModal
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Modale de création de conversation.
-->
<template>
  <div
    class="modal-backdrop-custom"
    role="dialog"
    aria-modal="true"
    aria-labelledby="new-conv-title"
    @click.self="$emit('close')"
    tabindex="-1"
    @keydown.esc="$emit('close')"
  >
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content p-3">
        <div class="modal-header">
          <h5 id="new-conv-title" class="modal-title">Nouvelle conversation</h5>
          <button type="button" class="btn-close" :disabled="busy" @click="$emit('close')"></button>
        </div>

        <form @submit.prevent="create">
          <div class="modal-body">
            <label class="form-label fw-semibold" for="conv-title">Titre <span class="text-muted fw-normal">(optionnel)</span></label>
            <input
              id="conv-title"
              ref="titleInput"
              v-model="title"
              type="text"
              class="form-control mb-3"
              placeholder="Ex. Escalade projet Titan"
              :disabled="busy"
              maxlength="120"
              autocomplete="off"
            />

            <label class="form-label fw-semibold" for="conv-participants">Participants (IDs)</label>
            <input
              id="conv-participants"
              v-model="participantsRaw"
              type="text"
              class="form-control"
              placeholder="Ex. 12, 34, 56"
              :disabled="busy"
              autocomplete="off"
            />
            <small class="text-muted">
              Pour l’instant : saisie libre d’IDs (on branchera la sélection de contacts ensuite).
            </small>

            <div v-if="error" class="alert alert-warning mt-3 mb-0" role="alert">
              {{ error }}
            </div>

            <div v-if="participantIds.length" class="small text-muted mt-2">
              {{ participantIds.length }} participant{{ participantIds.length > 1 ? 's' : '' }} sélectionné{{ participantIds.length > 1 ? 's' : '' }} — {{ participantIds.join(', ') }}
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" :disabled="busy" @click="$emit('close')">Annuler</button>
            <button type="submit" class="btn btn-primary" :disabled="busy || !canSubmit">
              <span v-if="busy" class="spinner-border spinner-border-sm me-1" role="status" aria-hidden="true"></span>
              <span v-else>Créer</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'

// ===== Props =====
const props = defineProps({
  busy: { type: Boolean, default: false },
})
// ===== Emissions =====
const emit = defineEmits(['close', 'create'])

const title = ref('')
const participantsRaw = ref('')
const error = ref('')

const participantIds = computed(() => {
  // "12, 34, abc, 12" -> [12, 34] (numériques, uniques)
  const ids = participantsRaw.value
    .split(',')
    .map(s => s.trim())
    .filter(Boolean)
    .map(s => Number(s))
    .filter(n => Number.isFinite(n))
  // dédoublonnage
  return Array.from(new Set(ids))
})

const canSubmit = computed(() => participantIds.value.length > 0)

function create() {
  error.value = ''
  if (!participantIds.value.length) {
    error.value = 'Veuillez indiquer au moins un participant (ID numérique).'
    return
  }
  emit('create', {
    title: title.value.trim(),
    participantIds: participantIds.value,
  })
}

const titleInput = ref(null)
onMounted(() => {
  // focus initial
  setTimeout(() => titleInput.value?.focus(), 0)
})
</script>

<style scoped src="@/assets/styles/messages.css"></style>
