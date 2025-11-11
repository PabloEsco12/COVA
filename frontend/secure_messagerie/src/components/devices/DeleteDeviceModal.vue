<template>
  <!-- fond -->
  <transition name="fade">
    <div v-if="show" class="modal-backdrop"></div>
  </transition>

  <!-- dialog -->
  <transition name="scale">
    <div v-if="show" class="modal-wrapper" @click.self="$emit('close')">
      <div class="modal-card modal-card--danger">
        <header class="modal-header">
          <div>
            <h5 class="mb-0 text-danger">Déconnecter l'appareil</h5>
            <small class="text-muted">L'appareil perdra son accès aux messages chiffrés.</small>
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
          <p>
            Es-tu sûr de vouloir déconnecter cet appareil ?
            <strong v-if="device && device.label">"{{ device.label }}"</strong>
          </p>
          <p class="text-muted small mb-0">
            Il devra être resynchronisé pour reprendre une session sécurisée.
          </p>

          <p v-if="error" class="alert alert-danger py-2 px-3 mt-3 mb-0">
            {{ error }}
          </p>
        </div>

        <footer class="modal-footer">
          <button class="btn btn-outline-secondary" type="button" @click="$emit('close')" :disabled="busy">
            Annuler
          </button>
          <button class="btn btn-danger" type="button" @click="$emit('confirm', device)" :disabled="busy">
            <span v-if="busy" class="spinner-border spinner-border-sm me-2"></span>
            Déconnecter
          </button>
        </footer>
      </div>
    </div>
  </transition>
</template>

<script setup>
defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  device: {
    type: Object,
    default: null,
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
defineEmits(['close', 'confirm'])
</script>

<style scoped src="@/assets/styles/devices.css"></style>
