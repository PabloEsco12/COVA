<!--
  ===== Component Header =====
  Component: RenameDeviceModal
  Author: Valentin Masurelle
  Date: 2025-11-26
  Role: Modale pour nommer ou renommer un appareil.
-->
<template>
  <!-- fond -->
  <transition name="fade">
    <div v-if="show" class="modal-backdrop"></div>
  </transition>

  <!-- carte -->
  <transition name="scale">
    <div v-if="show" class="modal-wrapper" @click.self="$emit('close')">
      <div class="modal-card">
        <header class="modal-header">
          <div>
            <h5 class="mb-0">Nommer cet appareil</h5>
            <small class="text-muted">Choisissez un nom facile à reconnaître.</small>
          </div>
          <button
            class="btn btn-sm btn-outline-secondary"
            type="button"
            @click="$emit('close')"
            :disabled="busy"
          >
            <i class="bi bi-x-lg"></i>
          </button>
        </header>

        <div class="modal-body">
          <label class="form-label small text-muted mb-1">Nom de l'appareil</label>
          <input
            v-model="name"
            type="text"
            class="form-control"
            maxlength="60"
            placeholder="Ex. Bureau · Chrome · Windows"
            :disabled="busy"
            @keyup.enter="confirm"
          />

          <p class="text-muted small mt-2">
            Astuce : ajoute le navigateur et l'OS, ça aide quand tu en as plusieurs.
          </p>

          <p v-if="error" class="alert alert-danger py-2 px-3 mt-3 mb-0">
            {{ error }}
          </p>
        </div>

        <footer class="modal-footer">
          <button class="btn btn-outline-secondary" type="button" @click="$emit('close')" :disabled="busy">
            Annuler
          </button>
          <button class="btn btn-primary" type="button" @click="confirm" :disabled="busy || !name.trim()">
            <span v-if="busy" class="spinner-border spinner-border-sm me-2"></span>
            Enregistrer
          </button>
        </footer>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch } from 'vue'

// ===== Props et emissions =====
const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  initialName: {
    type: String,
    default: '',
  },
  busy: {
    type: Boolean,
    default: false,
  },
  error: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['close', 'confirm'])

// ===== Etat local =====
const name = ref(props.initialName)

// ===== Synchronisation nom selon l'ouverture ou changement de prop =====
watch(
  () => props.show,
  (visible) => {
    if (visible) {
      name.value = props.initialName || ''
    }
  },
)

watch(
  () => props.initialName,
  (val) => {
    if (!props.show) return
    name.value = val || ''
  },
)

function confirm() {
  const clean = (name.value || '').trim()
  emit('confirm', clean)
}
</script>

<!-- ===== Styles de la modale rename ===== -->
<style scoped src="@/assets/styles/devices.css"></style>
