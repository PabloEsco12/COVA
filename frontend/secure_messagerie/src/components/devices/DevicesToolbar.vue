<template>
  <header class="page-header">
    <div>
      <h2 class="title">
        <i class="bi bi-phone me-2"></i>
        Appareils connectes
      </h2>
      <p class="subtitle">
        Surveillez les terminaux autorises et deconnectez les sessions douteuses en un clic.
      </p>
    </div>
    <div class="header-actions">
      <button
        class="btn btn-outline-danger"
        type="button"
        @click="$emit('logout-everywhere')"
        :disabled="logoutBusy || registering || loading"
      >
        <span v-if="logoutBusy" class="spinner-border spinner-border-sm me-2"></span>
        <span v-else class="me-2"><i class="bi bi-shield-x"></i></span>
        Deconnecter tous les appareils
      </button>
      <button
        class="btn btn-outline-secondary"
        type="button"
        @click="$emit('manual-sync')"
        :disabled="registering"
      >
        <span v-if="registering" class="spinner-border spinner-border-sm me-2"></span>
        <span v-else class="me-2"><i class="bi bi-arrow-repeat"></i></span>
        Synchroniser
      </button>
      <button
        class="btn btn-primary"
        type="button"
        @click="$emit('rename-current')"
        :disabled="registering"
      >
        <i class="bi bi-pencil-square me-2"></i>
        Nommer cet appareil
      </button>
    </div>
  </header>
</template>

<script setup>
defineProps({
  loading: Boolean,
  registering: Boolean,
  logoutBusy: Boolean,
})
defineEmits(['logout-everywhere', 'manual-sync', 'rename-current'])
</script>

<style scoped src="@/assets/styles/devices.css"></style>
