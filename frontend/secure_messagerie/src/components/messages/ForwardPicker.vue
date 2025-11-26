<!--
  ===== Component Header =====
  Component: ForwardPicker
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Sélecteur de conversations pour transférer un message.
-->
<template>
  <div
    v-if="open"
    class="forward-picker__backdrop"
    role="dialog"
    aria-modal="true"
    aria-label="Choisir la destination du transfert"
    @click="cancel"
  >
    <div class="forward-picker__panel" @click.stop>
      <header class="forward-picker__header">
        <p class="forward-picker__eyebrow">Transférer ce message</p>
        <div class="forward-picker__preview">
          <strong class="forward-picker__preview-author">
            {{ message?.displayName || 'Message sélectionné' }}
          </strong>
          <p class="forward-picker__preview-excerpt">{{ preview }}</p>
        </div>
        <button class="btn btn-link p-0" type="button" @click="cancel" aria-label="Fermer la sélection">
          <i class="bi bi-x-lg"></i>
        </button>
      </header>

      <div class="forward-picker__body">
        <div class="forward-picker__search">
          <input
            ref="inputRef"
            :value="query"
            type="search"
            class="form-control"
            placeholder="Rechercher une conversation"
            @input="$emit('update:query', $event.target.value)"
          />
        </div>
        <div v-if="targets.length" class="forward-picker__targets">
          <label>
            <input type="radio" :checked="false" class="d-none" />
          </label>
          <label v-for="target in targets" :key="target.id" class="forward-picker__item">
            <input
              class="form-check-input"
              type="radio"
              name="forward-target"
              :value="target.id"
              @change="$emit('select', target.id)"
            />
            <div class="forward-picker__item-body">
              <p class="mb-0 fw-semibold">{{ target.displayName }}</p>
              <small class="text-muted">{{ target.participantsLabel }}</small>
            </div>
          </label>
        </div>
        <p v-else class="forward-picker__empty">
          Aucune conversation ne correspond à votre recherche.
        </p>
      </div>

      <div class="forward-picker__actions">
        <router-link class="btn btn-outline-primary flex-grow-1" to="/dashboard/messages/new" @click="cancel">
          Nouvelle conversation
        </router-link>
        <button type="button" class="btn btn-light" @click="cancel">Annuler</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount, ref } from 'vue'

// ===== Props et etats =====
const props = defineProps({
  open: Boolean,
  message: Object,
  preview: {
    type: String,
    default: '',
  },
  query: {
    type: String,
    default: '',
  },
  targets: {
    type: Array,
    default: () => [],
  },
  allowKeyboard: {
    type: Boolean,
    default: true,
  },
})

// ===== Emissions =====
const emit = defineEmits(['update:query', 'select', 'cancel'])
const inputRef = ref(null)

function cancel() {
  emit('cancel')
}

function handleKeydown(event) {
  if (!props.open || !props.allowKeyboard) return
  if (event.key === 'Escape') {
    event.preventDefault()
    cancel()
  }
}

onMounted(() => {
  if (props.open) {
    inputRef.value?.focus()
  }
  window.addEventListener('keydown', handleKeydown)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleKeydown)
})

defineExpose({ inputRef })
</script>
